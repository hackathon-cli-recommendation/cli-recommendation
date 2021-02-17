from .util import get_latest_cmd, RecommendType


def analyze_personal_path(recommendation_result, command_list):
    if not recommendation_result or not command_list:
        return recommendation_result

    personal_command_list = get_latest_cmd(command_list, 0)
    personal_path = ','.join(personal_command_list)

    trigger_command_list = get_latest_cmd(command_list, 2)
    trigger_path = ','.join(trigger_command_list)

    path_array = personal_path.split(trigger_path)
    if not path_array or len(path_array) < 2:
        return recommendation_result

    path_array = path_array[1:]
    command_frequency = {}
    most_used_command = ""
    highest_frequency = 0
    for next_paths in path_array:
        if not next_paths:
            continue
        path_item = next_paths.split(',')
        if len(path_item) < 2:
            continue

        next_command = path_item[1]
        if next_command not in command_frequency:
            command_frequency[next_command] = 1
        else:
            command_frequency[next_command] = command_frequency[next_command] + 1
        if command_frequency[next_command] > highest_frequency:
            highest_frequency = command_frequency[next_command]
            most_used_command = next_command

    personalized_command_item = None
    for item in recommendation_result:
        if item['type'] == RecommendType.Command and item['command'] == most_used_command:
            personalized_command_item = item
            break
    if not personalized_command_item:
        return recommendation_result

    recommendation_result.remove(personalized_command_item)
    personalized_command_item['reason'] = 'You have used it in similar situations.'
    personalized_command_item['is_personalized'] = 1
    recommendation_result.insert(0, personalized_command_item)

    return recommendation_result
