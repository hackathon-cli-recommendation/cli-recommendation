import azure.functions as func
import json

from .cosmos_service import get_recommend_from_cosmos
from .aladdin_service import get_recommend_from_aladdin
from .util import need_aladdin_recommendation


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

    # get the recommendation of offline caculation from cosmos
    result = get_recommend_from_cosmos(command_list, recommend_type, top_num, error_info)

    # get the recommendation of offline caculation from aladdin
    if need_aladdin_recommendation(recommend_type):
        aladdin_result = get_recommend_from_aladdin(command_list, correlation_id, subscription_id, cli_version, user_id, top_num)
        result.extend(aladdin_result)

    # TODO SORT
    # TODO DUPLICATE

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
