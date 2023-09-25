import base64
import json
import logging
import os
from enum import Enum
from functools import wraps

import azure.functions as func
import jwt
import requests
from azure.functions import HttpRequest, HttpResponse
from common.exception import ParameterException
from jwt.algorithms import RSAAlgorithm

logger = logging.getLogger(__name__)


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


def verify_token(func):
    @wraps(func)
    def wrapper(req: HttpRequest) -> HttpResponse:
        token = req.headers.get('Authorization')
        if not token:
            return HttpResponse("Authorization token is missing", status_code=401)
        token = token.replace('Bearer ', '')
        parts = token.split(".")
        header = json.loads(base64.b64decode(parts[0] +"==").decode("utf-8")) 
        payload = json.loads(base64.b64decode(parts[1] +"==").decode("utf-8"))
        if 'alg' not in header or 'kid' not in header or 'azp' not in payload or 'aud' not in payload:
            print("Token is invalid.")
            return HttpResponse("Token is invalid", status_code=401)
        alg = header['alg']
        kid = header['kid']
        azp = payload['azp']
        aud = payload['aud']
        if azp not in os.environ.get("ALLOWED_APP_IDS", "40b5afcb-b0db-4d2c-83a0-083dbb8e0c14,19ab3e9c-cfdb-4d6e-8e4f-342ef4f9e97d,a942385d-6d3c-415b-bfbb-7f4350377466").split(','):
            logger.error("App ID is invalid.")
            return HttpResponse("App ID is invalid", status_code=401)

        tenant_id = os.environ.get("MICROSOFT_TENANT_ID", "72f988bf-86f1-41af-91ab-2d7cd011db47")
        jwks_url = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"

        response = requests.get(jwks_url)
        if response.status_code == 200:
            jwks = response.json()
        else:
            logger.error("Failed to retrieve JWKS:", response.status_code, response.text)
            return HttpResponse("Failed to retrieve JWKS", status_code=401)

        # Load AAD's public key from the retrieved key set
        public_key = None
        for key in jwks["keys"]:
            if key["kid"] == kid:
                public_key = RSAAlgorithm.from_jwk(json.dumps(key))
                break
        if public_key is None:
            logger.error("Failed to retrieve public key from JWKS")
            return HttpResponse("Failed to retrieve public key from JWKS", status_code=401)

        # Verify the JWT token: expiration, signature
        try:
            jwt.decode(token, public_key, algorithms=[alg], audience=aud)
            logger.info("token is valid")
        except jwt.InvalidTokenError as e:
            logger.error(f"Token validation failed: {e}")
            return HttpResponse(f"Token validation failed: {e}", status_code=401)
        return func(req)
    return wrapper
