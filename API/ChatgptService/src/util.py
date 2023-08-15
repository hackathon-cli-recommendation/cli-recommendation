from enum import Enum
import os
import azure.functions as func
import logging
import json

from .exception import ParameterException


def get_param(req: func.HttpRequest, name: str, required=True, default=None):
    value = req.params.get(name)
    if not value:
        try:
            req_body = req.get_json()
            value = req_body.get(name)
        except ValueError:
            pass
    if required and value is None:
        raise ParameterException(
            f'Illegal parameter: please pass in the parameter "{name}"')
    elif value is None:
        return default
    return value


def get_param_str(req: func.HttpRequest, name: str, required=False, default=""):
    value = get_param(req, name, required, default)
    if not isinstance(value, str):
        raise ParameterException(
            f'Illegal parameter: the parameter "{name}" must be the type of string')
    return value


def get_param_list(req: func.HttpRequest, name: str, required=False, default=[]):
    value = get_param(req, name, required, default)
    try:
        return list(value)
    except ValueError:
        raise ParameterException(
            f'Illegal parameter: the parameter "{name}" must be the type of list')


def is_valid_json(json_str):
    try:
        json.loads(json_str)
        return True
    except json.JSONDecodeError:
        return False
