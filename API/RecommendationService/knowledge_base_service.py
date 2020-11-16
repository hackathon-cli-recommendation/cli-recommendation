import os

from azure.cosmos import CosmosClient, PartitionKey
from .util import get_latest_cmd, generated_query_kql


def get_recommend_from_knowledge_base(command_list, recommend_type, error_info, top_num=50):

    command = get_latest_cmd(command_list)

    client = CosmosClient(os.environ["CosmosDB_Endpoint"], os.environ["CosmosDB_Key"])
    database = client.create_database_if_not_exists(id=os.environ["CosmosDB_DataBase"])
    knowledge_base_container = database.create_container_if_not_exists(id=os.environ["KnowledgeBase_Container"], partition_key=PartitionKey(path="/command"))

    query = generated_query_kql(command, recommend_type, error_info)

    result = []
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

            if len(result) >= top_num:
                return result[0: top_num]

    return result
