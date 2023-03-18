import json
import os
import asyncio

import azure.functions as func

from .aladdin_service import get_recommend_from_aladdin
from .filter import filter_recommendation_result
from .knowledge_base_service import get_recommend_from_knowledge_base
from .offline_data_service import get_recommend_from_offline_data, get_recommend_from_solution
from .personalized_analysis import analyze_personal_path
from .scenario_service import get_scenario_recommendation_from_search
from .util import get_success_commands, load_command_list, need_aladdin_recommendation, need_offline_recommendation, need_scenario_recommendation, need_solution_recommendation
import uuid
import time
def main(req: func.HttpRequest) -> func.HttpResponse:

    try:
        command_list = get_param_str(req, 'command_list')
        if not command_list:
            return func.HttpResponse('Illegal parameter: please pass in the parameter "command_list"', status_code=400)
    except ValueError as e:
        return func.HttpResponse('Illegal parameter: the parameter "command_list" must be the type of string', status_code=400)

    # Parameter `top_num` is optional. If there is no `command_top_num` or `scenario_top_num`, the corresponding top_num will fall back to this value.
    try:
        top_num = get_param_int(req, 'top_num')
        top_num = top_num if top_num is not None else 5
    except ValueError:
        return func.HttpResponse('Illegal parameter: the parameter "top_num" must be the type of int', status_code=400)

    try:
        command_top_num = get_param_int(req, 'command_top_num')
        command_top_num = command_top_num if command_top_num is not None else top_num
    except ValueError:
        return func.HttpResponse('Illegal parameter: the parameter "command_top_num" must be the type of int', status_code=400)

    try:
        scenario_top_num = get_param_int(req, 'scenario_top_num')
        scenario_top_num = scenario_top_num if scenario_top_num is not None else top_num
    except ValueError:
        return func.HttpResponse('Illegal parameter: the parameter "scenario_top_num" must be the type of int', status_code=400)

    try:
        recommend_type = get_param_int(req, 'type')
    except ValueError:
        return func.HttpResponse('Illegal parameter: the parameter "type" must be the type of int', status_code=400)

    try:
        error_info = get_param_str(req, 'error_info')
        if error_info == 'show help':
            error_info = ''
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

    result = asyncio.run(get_recommendation_items(command_list, recommend_type, error_info, correlation_id, subscription_id, cli_version, user_id, command_top_num, scenario_top_num))

    if not result:
        return func.HttpResponse('{}', status_code=200)

    return func.HttpResponse(generate_response(data=result, status=200))


async def get_recommendation_items(command_list, recommend_type, error_info, correlation_id, subscription_id, cli_version, user_id, command_top_num=5, scenario_top_num=5):
    command_list = load_command_list(command_list)
    success_command_list = get_success_commands(command_list)

    # Take the data of knowledge base first, when the quantity of knowledge base is not enough, then take the data from calculation and Aladdin
    knowledge_base_items_task = asyncio.create_task(asyncio.to_thread(get_recommend_from_knowledge_base, command_list, recommend_type, error_info))

    # Get the recommendation of offline caculation from offline data
    # Since the `get_recommend_from_offline_data` method is already an async function, so we don't need to create a new thread for it to run in.
    calculation_items_task = None
    if need_offline_recommendation(recommend_type):
        calculation_items_task = asyncio.create_task(get_recommend_from_offline_data(success_command_list, recommend_type, top_num=command_top_num))

    # Get the recommendation from Aladdin
    aladdin_items_task = None
    if need_aladdin_recommendation(recommend_type):
        aladdin_items_task = asyncio.create_task(asyncio.to_thread(get_recommend_from_aladdin, success_command_list, correlation_id, subscription_id, cli_version, user_id, command_top_num))

    # Get the recommendation from E2E Scenarios
    scenario_items_task = None
    if need_scenario_recommendation(recommend_type):
        scenario_items_task = asyncio.create_task(asyncio.to_thread(get_scenario_recommendation_from_search, success_command_list, scenario_top_num))

    # Get Solution recommendation
    solution_items_task = None
    if need_solution_recommendation(recommend_type, error_info):
        solution_items_task = asyncio.create_task(asyncio.to_thread(get_recommend_from_solution, command_list, recommend_type, error_info, top_num=command_top_num))

    solution_items = await solution_items_task if solution_items_task else []
    calculation_items = await calculation_items_task if calculation_items_task else []
    knowledge_base_items = await knowledge_base_items_task if knowledge_base_items_task else []
    aladdin_items = await aladdin_items_task if aladdin_items_task else []
    scenario_items = await scenario_items_task if scenario_items_task else []

    result = merge_and_sort_recommendation_items(solution_items + knowledge_base_items, calculation_items, aladdin_items)
    result.extend(scenario_items)

    if os.environ["Support_Personalization"] == '1':
        result = analyze_personal_path(result, command_list)

    result = filter_recommendation_result(result, success_command_list, command_top_num, scenario_top_num)

    return result


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
        'status': status,
        # The dynamic version of the API, which is defined in the function app settings and can be changed without redeploying the whole function.
        # The version is different from the version of the whole api function, which is defined in host.json.
        'dynamic_api_version': os.environ["Dynamic_API_Version"]
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
