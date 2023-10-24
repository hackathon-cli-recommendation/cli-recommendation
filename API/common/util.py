
import json
import os

from enum import Enum
import azure.functions as func
from rapidfuzz import fuzz

from common.exception import ParameterException


class ScenarioSourceType(int, Enum):
    SAMPLE_REPO = 1
    DOC_CRAWLER = 2
    MANUAL_INPUT = 3


def get_param(req: func.HttpRequest, name: str, required=False, default=None):
    value = req.params.get(name)
    if not value:
        try:
            req_body = req.get_json()
            value = req_body.get(name)
        except ValueError:
            pass
    if required and value is None:
        raise ParameterException(f'Illegal parameter: please pass in the parameter "{name}"')
    elif value is None:
        return default
    return value


def get_param_str(req: func.HttpRequest, name: str, required=False, default=""):
    value = get_param(req, name, required, default)
    if not isinstance(value, str):
        raise ParameterException(f'Illegal parameter: the parameter "{name}" must be the type of string')
    return value


def get_param_int(req: func.HttpRequest, name: str, required=False, default=0):
    try:
        return int(get_param(req, name, required, default))
    except ValueError:
        raise ParameterException(f'Illegal parameter: the parameter "{name}" must be the type of int')


def get_param_list(req: func.HttpRequest, name: str, required=False, default=[]):
    value = get_param(req, name, required, default)
    try:
        return list(value)
    except ValueError:
        raise ParameterException(
            f'Illegal parameter: the parameter "{name}" must be the type of list')


def get_param_enum(req: func.HttpRequest, name: str, cls, required=False, default=None, match_case=False):
    value = get_param(req, name, required)
    lut = {}
    for enum_kv in cls:
        if match_case:
            lut[str(enum_kv.value)] = enum_kv
        else:
            lut[str(enum_kv.value).upper()] = enum_kv
    if value is None:
        return default
    elif value.upper() in lut:
        return lut[value.upper()]
    else:
        raise ParameterException(f'Illegal parameter: the parameter "{name}" must be in [{", ".join([enum_kv.value for enum_kv in cls])}]')


def generate_response(data, status, error=None):
    response_data = {
        'data': data,
        'error': error,
        'status': status,
        # The version of the API, which is defined in the function app settings and can be changed without redeploying the whole function.
        'api_version': os.environ["API_Version"]
    }
    return json.dumps(response_data)


def determine_strings_are_similar(str1, str2):
    return fuzz.token_sort_ratio(str1, str2) >= float(os.environ["KEYWORD_SIMILARITY_SCORE"])


def parse_command_info(command_info):
    if not command_info:
        return "", []

    command_items = command_info.split()
    arguments_start = False
    arguments_part = []
    command_part = []
    for item in command_items:
        if item.startswith('-'):
            arguments_start = True
            arguments_part.append(item)
        elif not arguments_start:
            command_part.append(item)

    command_signature = ' '.join(command_part)
    return command_signature, arguments_part
