import json
import logging
import os

from enum import Enum
from rapidfuzz import fuzz


logger = logging.getLogger(__name__)


class ScenarioSourceType(int, Enum):
    SAMPLE_REPO = 1
    DOC_CRAWLER = 2
    MANUAL_INPUT = 3


def generate_response(data, status, error=None):
    response_data = {
        'data': data if data != [None] else [],
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
