import os
import json


def generate_response(data, status, error=None):
    response_data = {
        'data': data,
        'error': error,
        'status': status,
        # The version of the API, which is defined in the function app settings and can be changed without redeploying the whole function.
        'api_version': os.environ["API_Version"]
    }
    return json.dumps(response_data)
