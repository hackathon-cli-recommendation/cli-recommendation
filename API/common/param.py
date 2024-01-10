import logging

import azure.functions as func

from common.exception import ParameterException


logger = logging.getLogger(__name__)


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
