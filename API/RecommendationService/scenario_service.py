import os
from typing import List

from azure.cosmos import CosmosClient, PartitionKey

from .util import (RecommendationSource, RecommendType, ScenarioSourceType,
                   get_latest_cmd)


def get_scenario_recommendation(command_list, top_num=50):
    source_type: List[ScenarioSourceType] = [ScenarioSourceType.SAMPLE_REPO]

    commands = get_latest_cmd(command_list)

    client = CosmosClient(os.environ["CosmosDB_Endpoint"], os.environ["CosmosDB_Key"])
    database = client.create_database_if_not_exists(id=os.environ["CosmosDB_DataBase"])
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
                'nextCommandSet': item['commandSet'][1:],
                'source': RecommendationSource.OfflineCaculation,
                'type': RecommendType.Scenario
            }
            if 'description' in item:
                scenario['reason'] = item['description']
            result.append(scenario)

    if len(result) >= top_num:
        return result[0: top_num]

    return result
