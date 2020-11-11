import os
import json

from azure.cosmos import CosmosClient, PartitionKey
from .util import generated_cosmos_type, need_error_info, parse_error_info


def get_recommend_from_cosmos(command_list, recommend_type, top_num, error_info):

    command = get_latest_cmd(command_list)

    client = CosmosClient(os.environ["CosmosDB_Endpoint"], os.environ["CosmosDB_Key"])
    database = client.create_database_if_not_exists(id=os.environ["CosmosDB_DataBase"])
    recommendation_container = database.create_container_if_not_exists(id=os.environ["Recommendation_Container"], partition_key=PartitionKey(path="/command"))
    knowledge_base_container = database.create_container_if_not_exists(id=os.environ["KnowledgeBase_Container"], partition_key=PartitionKey(path="/command"))

    query = "SELECT * FROM c WHERE c.command = '{}' ".format(command)

    cosmos_type =  generated_cosmos_type(recommend_type, error_info)
    if isinstance(cosmos_type, str):
        query += " and c.type in ({}) ".format(cosmos_type)
    elif isinstance(cosmos_type, int):
        query += " and c.type = {} ".format(cosmos_type)

    # If there is an error message, recommend the solution first
    if error_info and need_error_info(recommend_type):
        error_info_arr = parse_error_info(error_info)
        for info in error_info_arr:
            query += " and CONTAINS(c.errorInformation, '{}', true) ".format(info)

    result = []

    # load bussniss knowleage
    knowledge_base_items = list(knowledge_base_container.query_items(query=query, enable_cross_partition_query=True))
    if knowledge_base_items:
        for item in knowledge_base_items:
            if 'nextCommandSet' in item:
                scenario = {
                    'scenario': item['scenario'],
                    'nextCommandSet': item['nextCommandSet']
                }
                if 'reason' in item:
                    scenario['reason'] = item['reason']
                result.append(scenario)

            if 'nextCommand' in item:
                for command_info in item['nextCommand']:
                    result.append(command_info)

    # load recommendation items
    query_items = list(recommendation_container.query_items(query=query, enable_cross_partition_query=True))

    recommendation_items = []
    for item in query_items:
        if item and 'nextCommand' in item:
            for command_info in item['nextCommand']:
                command_info['ratio'] = float((int(command_info['count'])/int(item['totalCount'])))
                if command_info['ratio'] * 100 >= int(os.environ["Recommendation_Threshold"]):
                    recommendation_items.append(command_info)

    if recommendation_items:
        recommendation_items = sorted(recommendation_items, key=lambda x: x['ratio'], reverse=True)
        result.extend(recommendation_items)

    if top_num:
        result = result[0: top_num]

    return result


def get_latest_cmd(command_list):
    command_data = json.loads(command_list)
    # If there is no command has been executed before, assume that the user's first command is "group create"
    if len(command_data) == 0:
        return "group create"
    latest_cmd = json.loads(command_data[-1])
    return latest_cmd['command']
