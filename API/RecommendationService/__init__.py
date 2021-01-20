import azure.functions as func
import json
import os

from functools import reduce

from .knowledge_base_service import get_recommend_from_knowledge_base
from .offline_data_service import get_recommend_from_offline_data
from .aladdin_service import get_recommend_from_aladdin

from .util import need_aladdin_recommendation
from .filter import filter_recommendation_result


def main(req: func.HttpRequest) -> func.HttpResponse:

    try:
        command_list = get_param_str(req, 'command_list')
        if not command_list:
            return func.HttpResponse('Illegal parameter: please pass in the parameter "command_list"', status_code=400)
    except ValueError:
        return func.HttpResponse('Illegal parameter: the parameter "command_list" must be the type of string', status_code=400)

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

    try:
        correlation_id = get_param_str(req, 'correlation_id')
    except ValueError:
        return func.HttpResponse('Illegal parameter: the parameter "correlation_id" must be the type of string', status_code=400)

    try:
        subscription_id = get_param_str(req, 'subscription_id')
    except ValueError:
        return func.HttpResponse('Illegal parameter: the parameter "subscription_id" must be the type of string', status_code=400)

    try:
        cli_version = get_param_str(req, 'cli_version')
    except ValueError:
        return func.HttpResponse('Illegal parameter: the parameter "cli_version" must be the type of string', status_code=400)

    try:
        user_id = get_param_str(req, 'user_id')
    except ValueError:
        return func.HttpResponse('Illegal parameter: the parameter "user_id" must be the type of string', status_code=400)

    # Take the data of knowledge base first, when the quantity of knowledge base is not enough, then take the data from calculation and Aladdin
    knowledge_base_items = get_recommend_from_knowledge_base(command_list, recommend_type, error_info)
    if len(knowledge_base_items) >= top_num:
        result = filter_recommendation_result(knowledge_base_items, command_list)
        return func.HttpResponse(generate_response(data=result[0: top_num], status=200))

    # Get the recommendation of offline caculation from offline data
    calculation_items = get_recommend_from_offline_data(command_list, recommend_type, error_info)

    # Get the recommendation from Aladdin
    aladdin_items = []
    if need_aladdin_recommendation(recommend_type, error_info):
        aladdin_items = get_recommend_from_aladdin(command_list, correlation_id, subscription_id, cli_version, user_id)

    result = merge_and_sort_recommendation_items(knowledge_base_items, calculation_items, aladdin_items)
    result = filter_recommendation_result(result, command_list)

    if not result:
        return func.HttpResponse('{}', status_code=200)

    return func.HttpResponse(generate_response(data=result[0:top_num], status=200))


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


# Merge and sort multiple data sources
def merge_and_sort_recommendation_items(knowledge_base_items, calculation_items, aladdin_items):

    result = knowledge_base_items

    # Record recommended commands for duplicate removal
    exist_commands = []
    if knowledge_base_items:
        for item in knowledge_base_items:
            if 'command' in item:
                exist_commands.append(item['command'])

    # Merge calculation_items and aladdin_items, and sort them interleaved
    command_index = 0
    commands_from_recommendation = []
    while(command_index < len(calculation_items) and command_index < len(aladdin_items)):
        aladdin_command = aladdin_items[command_index]['command']
        calculation_command = calculation_items[command_index]['command']

        if os.environ["Recommendation_Prefer"] == "1":
            if calculation_command not in exist_commands:
                commands_from_recommendation.append(calculation_items[command_index])
                exist_commands.append(calculation_command)
            if aladdin_command not in exist_commands:
                commands_from_recommendation.append(aladdin_items[command_index])
                exist_commands.append(aladdin_command)

        else:
            if aladdin_command not in exist_commands:
                commands_from_recommendation.append(aladdin_items[command_index])
                exist_commands.append(aladdin_command)
            if calculation_command not in exist_commands:
                commands_from_recommendation.append(calculation_items[command_index])
                exist_commands.append(calculation_command)

        command_index = command_index + 1

    commands_from_recommendation = merge_remaining_items(command_index, calculation_items, exist_commands, commands_from_recommendation)
    commands_from_recommendation = merge_remaining_items(command_index, aladdin_items, exist_commands, commands_from_recommendation)

    result.extend(commands_from_recommendation)
    return result


def merge_remaining_items(command_index, items, exist_commands, commands_from_recommendation):

    while command_index < len(items):

        command = items[command_index]['command']
        if command not in exist_commands:
            commands_from_recommendation.append(items[command_index])
            exist_commands.append(command)

        command_index = command_index + 1

    return commands_from_recommendation
