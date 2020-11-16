import os

from azure.cosmos import CosmosClient, PartitionKey
from .util import get_latest_cmd, generated_query_kql


def get_recommend_from_cosmos(command_list, recommend_type, error_info, top_num=50):

    command = get_latest_cmd(command_list)

    client = CosmosClient(os.environ["CosmosDB_Endpoint"], os.environ["CosmosDB_Key"])
    database = client.create_database_if_not_exists(id=os.environ["CosmosDB_DataBase"])
    recommendation_container = database.create_container_if_not_exists(id=os.environ["Recommendation_Container"], partition_key=PartitionKey(path="/command"))

    query = generated_query_kql(command, recommend_type, error_info)

    query_items = list(recommendation_container.query_items(query=query, enable_cross_partition_query=True))

    result = []
    for item in query_items:
        if item and 'nextCommand' in item:
            for command_info in item['nextCommand']:
                command_info['ratio'] = float((int(command_info['count'])/int(item['totalCount'])))
                if command_info['ratio'] * 100 >= int(os.environ["Recommendation_Threshold"]):
                    result.append(command_info)

    # Sort the calculated offline data according to the usage ratio and take the top n data
    if result:
        result = sorted(result, key=lambda x: x['ratio'], reverse=True)

    return result[0: top_num]
