import os
from typing import List

from azure.core.credentials import AzureKeyCredential
from azure.cosmos import CosmosClient, PartitionKey
from azure.search.documents import SearchClient

from .util import (RecommendationSource, RecommendType, ScenarioSourceType,
                   get_latest_cmd)


def strip_az_in_command_set(command_set):
    """Remove `az ` in commands in command_set

    Args:
        command_set (list[dict]): list of commands

    Returns:
        list[dict]: list of filtered commands
    """
    result = []
    for command in command_set:
        if command["command"] and command["command"].startswith("az "):
            command["command"] = command["command"][3:]
            result.append(command)
    return result


def get_scenario_recommendation(command_list, top_num=50):
    source_type: List[ScenarioSourceType] = [ScenarioSourceType.SAMPLE_REPO]

    commands = get_latest_cmd(command_list)

    client = CosmosClient(os.environ["CosmosDB_Endpoint"], os.environ["CosmosDB_Key"])
    database = client.get_database_client(id=os.environ["CosmosDB_DataBase"])
    e2e_scenario_container = database.create_container_if_not_exists(id=os.environ["E2EScenario_Container"], partition_key=PartitionKey(path="/firstCommand"))

    result = []
    qry = f'SELECT * FROM c where c.firstCommand = @cmd and c.source in ({",".join(["@src"+str(int(src)) for src in source_type])})'
    for item in e2e_scenario_container.query_items(
        query=qry,
        parameters=[
            {"name": "@cmd", "value": "az " + commands[-1]},
        ] + [{"name": "@src"+str(int(src)), "value": src} for src in source_type],
        enable_cross_partition_query=True,
    ):
        if len(item['commandSet']) > 1:
            scenario = {
                'scenario': item['name'],
                'nextCommandSet': strip_az_in_command_set(item['commandSet'][1:]),
                'source': RecommendationSource.OfflineCaculation,
                'type': RecommendType.Scenario
            }
            if 'description' in item:
                scenario['reason'] = item['description']
            result.append(scenario)

    if len(result) >= top_num:
        return result[0: top_num]

    return result


def get_search_results(trigger_commands: List[str], top: int = 5):
    """Search related sceanrios using cognitive search

    Args:
        trigger_commands (List[str]): list of commands used to search
        top (int, optional): top num of returned results. Defaults to 5.

    Returns:
        list[dict]: searched scenarios
    """
    if len(trigger_commands) == 0:
        return []
    service_endpoint = os.environ["SCENARIO_SEARCH_SERVICE_ENDPOINT"]
    search_client = SearchClient(endpoint=service_endpoint,
                                 index_name=os.environ["SCENARIO_SEARCH_INDEX"],
                                 credential=AzureKeyCredential(os.environ["SCENARIO_SEARCH_SERVICE_SEARCH_KEY"]))

    search_statement = "(" + " OR ".join([f'"{cmd}"' for cmd in trigger_commands][:-1]) + ") AND " + f'"{trigger_commands[-1]}"'
    search_statement = f'"{trigger_commands[-1]}" OR ({search_statement})'
    results = search_client.search(
        search_text=search_statement,
        include_total_count=True,
        search_fields=["commandSet/command"],
        highlight_fields="commandSet/command",
        top=top,
        query_type='full')
    results = list(results)
    return results


def get_scenario_recommendation_from_search(command_list, top_num=5):
    """Recommend Scenarios that current context could be in

    Args:
        command_list (list[str]): commands used to trigger
        top_num (int, optional): top num of recommended results. Defaults to 5.

    Returns:
        list[dict]: searched scenarios
    """
    if len(command_list) == 0:
        return []
    trigger_len = int(os.environ.get("ScenarioRecommendationTriggerLength", "3"))
    trigger_commands = get_latest_cmd(command_list, trigger_len)
    trigger_commands = [cmd[3:] if cmd.startswith("az ") else cmd for cmd in trigger_commands]
    searched = get_search_results(trigger_commands, top_num)

    results = []
    for item in searched:
        cmds = [(idx, cmd['command'][3:]) for idx, cmd in enumerate(item['commandSet']) if len(cmd) > 3]
        exec_idx = [cmd[0] for cmd in cmds if cmd[1] not in trigger_commands]
        if len(cmds) - 1 not in exec_idx:
            continue
        scenario = {
            'scenario': item['name'],
            'nextCommandSet': strip_az_in_command_set(item['commandSet']),
            'source': RecommendationSource.Search,
            'type': RecommendType.Scenario,
            'execIdx': exec_idx,
            'score': item['@search.score']
        }
        if 'description' in item:
            scenario['reason'] = item['description']
        results.append(scenario)
    return results
