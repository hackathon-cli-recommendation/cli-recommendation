from azure.cosmos import exceptions, CosmosClient, PartitionKey

import logging
import azure.functions as func
import os
import json


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

    client = CosmosClient(os.environ["CosmosDB_Endpoint"], os.environ["CosmosDB_Key"])
    database = client.create_database_if_not_exists(id="cli-recommendation")
    container = database.create_container_if_not_exists(id="recommendation-without-arguments", partition_key=PartitionKey(path="/command"))

    query = "SELECT * FROM c WHERE c.command = '{}' ".format(command)
    query_items = list(container.query_items(query=query, enable_cross_partition_query=True))

    if not query_items:
        return func.HttpResponse('{}', status_code=200)

    result = []
    for item in query_items:
        if item and 'nextCommand' in item:
            for command_info in item['nextCommand']:
                if not recommend_type or recommend_type == command_info['type']:
                    command_info['ratio'] = float((int(command_info['count'])/int(item['totalCount'])))
                    result.append(command_info)

    if top_num:
        result = result[0: top_num]

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
