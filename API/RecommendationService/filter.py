import json

from .util import RecommendType


def filter_recommendation_result(recommendation_result, command_list, command_top_num=5, scenario_top_num=5):
    if not recommendation_result or not command_list:
        return recommendation_result
    command_data = json.loads(command_list)
    if len(command_data) == 0:
        return recommendation_result

    filter_command = json.loads(command_data[-1])['command']
    scenario_count = 0
    command_count = 0
    filter_result = []
    for item in recommendation_result:
        if item['type'] != RecommendType.Scenario:
            if item['type'] == RecommendType.Command:
                if item['command'] == filter_command or 'delete' in item['command']:
                    continue
            if command_count >= command_top_num:
                continue
            else:
                command_count += 1
        else:
            if scenario_count >= scenario_top_num:
                continue
            else:
                scenario_count += 1
        filter_result.append(item)

    return filter_result
