import json

from .util import RecommendType


def filter_recommendation_result(recommendation_result, command_list):
    if not recommendation_result or not command_list:
        return recommendation_result
    command_data = json.loads(command_list)
    if len(command_data) == 0:
        return recommendation_result

    filter_command = json.loads(command_data[-1])['command']
    filter_result = []
    for item in recommendation_result:
        if item['type'] == RecommendType.Command and item['command'] == filter_command:
            continue
        filter_result.append(item)

    return filter_result
