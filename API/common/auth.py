
import base64
import json
import logging
import os
from functools import wraps

import jwt
import requests
from azure.identity import DefaultAzureCredential
from azure.functions import HttpResponse
from jwt.algorithms import RSAAlgorithm

logger = logging.getLogger(__name__)


def verify_token(func):
    @wraps(func)
    def wrapper(*args, **kwargs) -> HttpResponse:
        token = kwargs['req'].headers.get('Authorization')
        if not token:
            return HttpResponse("Authorization token is missing", status_code=401)
        token = token.replace('Bearer ', '')
        parts = token.split(".")
        header = json.loads(base64.b64decode(parts[0] +"==").decode("utf-8")) 
        payload = json.loads(base64.b64decode(parts[1] +"==").decode("utf-8"))
        if 'alg' not in header or 'kid' not in header or 'aud' not in payload or ('azp' not in payload and 'appid' not in payload):
            logger.error("Token is invalid.")
            return HttpResponse("Token is invalid", status_code=401)
        alg = header['alg']
        kid = header['kid']
        azp = payload['azp'] if 'azp' in payload else payload['appid']
        aud = payload['aud']
        if azp not in os.environ["ALLOWED_APP_IDS"].split(','):
            logger.error("App ID is invalid.")
            return HttpResponse("App ID is invalid", status_code=401)

        tenant_id = os.environ["MICROSOFT_TENANT_ID"]
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
        return func(*args, **kwargs)
    return wrapper


def _get_auth_token(*scopes: str):
    try:
        credential = DefaultAzureCredential()
        token = credential.get_token(*scopes)
        token = "Bearer " + token.token
        return token
    except Exception as e:
        logger.error("Failed to get auth token: %s", e)
        return None


def get_auth_token_for_learn_knowlegde_index():
    scope = os.environ["LEARN_KNOWLEDGE_INEX_SCOPE"]
    return _get_auth_token(scope)
