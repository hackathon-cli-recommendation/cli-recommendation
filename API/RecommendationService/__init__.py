from azure.cosmos import exceptions, CosmosClient, PartitionKey

import logging
import azure.functions as func
import os
import json
from .util import generated_cosmos_type, need_error_info, parse_error_info


def main(req: func.HttpRequest) -> func.HttpResponse:

    try:
        command = get_param_str(req, 'command')
        if not command:
            return func.HttpResponse('Illegal parameter: please pass in the parameter "command"', status_code=400)
    except ValueError:
        return func.HttpResponse('Illegal parameter: the parameter "command" must be the type of string', status_code=400)

    try:
        top_num = get_param_int(req, 'top_num')
    except ValueError:
        return func.HttpResponse('Illegal parameter: the parameter "top_num" must be the type of int', status_code=400)

    try:
        recommend_type = get_param_int(req, 'type')
    except ValueError:
        return func.HttpResponse('Illegal parameter: the parameter "type" must be the type of int', status_code=400)

    try:
        error_info = get_param_str(req, 'error_info')
    except ValueError:
        return func.HttpResponse('Illegal parameter: the parameter "error_info" must be the type of string', status_code=400)

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

    if not result:
        return func.HttpResponse('{}', status_code=200)

    return func.HttpResponse(generate_response(data=result, status=200))


def get_param_str(req, param_name):
    param = req.params.get(param_name)
    if not param:
        try:
            if not req.get_body():
                return None
            req_body = req.get_json()
        except ValueError as ex:
            raise ex
        else:
            param = req_body.get(param_name)
    return param


def get_param_int(req, param_name):
    param = get_param_str(req, param_name)
    if param:
        try:
            param = int(param)
        except ValueError as ex:
            raise ex
    return param


def generate_response(data, status, error=None):
    response_data = {
        'data': data,
        'error': error,
        'status': status
    }
    return json.dumps(response_data)
