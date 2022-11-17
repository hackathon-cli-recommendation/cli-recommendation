import os

from azure.cosmos import CosmosClient

from .util import generated_query_kql

client = CosmosClient(os.environ["CosmosDB_Endpoint"], os.environ["CosmosDB_Key"])
database = client.get_database_client(os.environ["CosmosDB_DataBase"])
knowledge_base_container = database.get_container_client(os.environ["KnowledgeBase_Container"])
recommendation_container = database.get_container_client(os.environ["Recommendation_Container"])
recommendation_container_2 = database.get_container_client(os.environ["Recommendation_Container_2"])
e2e_scenario_container = database.get_container_client(os.environ["E2EScenario_Container"])


def query_recommendation_from_knowledge_base(prev_command, recommend_type, error_info):
    query = generated_query_kql(prev_command, recommend_type, error_info)

    return knowledge_base_container.query_items(query=query, enable_cross_partition_query=True)


def query_recommendation_from_offline_data(prev_command, recommend_type, error_info):
    query = generated_query_kql(prev_command, recommend_type, error_info)

    return recommendation_container.query_items(query=query, enable_cross_partition_query=True)


def query_recommendation_from_offline_data_2(pprev_command, prev_command, recommend_type, error_info):
    query = generated_query_kql(pprev_command + "|" + prev_command, recommend_type, error_info)

    return recommendation_container_2.query_items(query=query, enable_cross_partition_query=True)


def query_recommendation_from_e2e_scenario(prev_command, source_type):
    qry = f'SELECT * FROM c where c.firstCommand = @cmd and c.source in ({",".join(["@src"+str(int(src)) for src in source_type])})'
    return e2e_scenario_container.query_items(
        query=qry,
        parameters=[
            {"name": "@cmd", "value": "az " + prev_command},
        ] + [{"name": "@src"+str(int(src)), "value": src} for src in source_type],
        enable_cross_partition_query=True,
    )
