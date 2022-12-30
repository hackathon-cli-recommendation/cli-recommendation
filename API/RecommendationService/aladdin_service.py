import os
import requests
import json
import logging
from .util import RecommendationSource, RecommendType


async def get_recommend_from_aladdin(command_list, correlation_id, subscription_id, cli_version, user_id, top_num=50):  # pylint: disable=unused-argument
    '''query next command from web api'''

    url = os.environ["Aladdin_Service_URL"]

    headers = {
        'Content-Type': 'application/json'
    }
    if user_id:
        headers["X-UserId"] = user_id

    payload = {
        "history": get_cmd_history(command_list),
        "clientType": "AzureCli",
        "context": {
            "versionNumber": cli_version    
        },
        "numberOfPredictions": top_num,
        "useDefault": False
    }
    if correlation_id:
        payload["context"]["CorrelationId"] = correlation_id
    if subscription_id:
        payload["context"]["SubscriptionId"] = subscription_id

    response = requests.post(url, json.dumps(payload), headers=headers)
    if response.status_code != 200:
        logging.info('Status:{} {} ErrorMessage:{}'.format(response.status_code, response.reason, response.text))
        return []
    return transform_response(response)


def get_cmd_history(command_list):
    if len(command_list) == 0:
        return ["start_of_snippet", "start_of_snippet"]
    if len(command_list) == 1 or os.environ["Aladdin_History_Command"] == "1":
        return ["start_of_snippet", get_cmd_data(command_list[-1])]
    return [get_cmd_data(command_list[-2]), get_cmd_data(command_list[-1])] 


def get_cmd_data(command_item):
    command_data = command_item['command']
    if 'arguments' in command_item:
        # parameters in the model is already sorted in alphabetical order, so the parameters we pass in should also keep this rule
        command_item['arguments'] = sorted(command_item['arguments'])
        command_data = '{} {}'.format(command_data, ' *** '.join(command_item['arguments']) + ' ***')
    return command_data


def transform_response(response):
    response_data = json.loads(response.text)
    result = []

    for recommended_item in response_data: 
        if 'command' not in recommended_item or not recommended_item['command']:
            continue

        cmd_items = recommended_item['command'].split()

        sub_commands = []
        arguments = []
        argument_start = False
        argument_values = {}
        values = []
        for item in cmd_items:
            if item.startswith('-'):
                argument_start = True
                # In the case of "positional arguments" and "no arguments", the value of item is '-' 
                if item != '-':
                    if values and arguments:
                        argument_values[arguments[-1]] = values
                        values = []
                    arguments.append(item)
            elif not argument_start and not item.startswith('<'):
                sub_commands.append(item)
            else:
                values.append(item)
        if values and arguments:
            argument_values[arguments[-1]] = values

        example = ' '.join(sub_commands)
        for argument in arguments:
            example = example + ' ' + argument
            if argument in argument_values and argument_values[argument]:
                arg_values = ' '.join(argument_values[argument])
                if arg_values.startswith('<'):
                    example = example + ' ' + arg_values
                else:
                    example = example + ' <' +  arg_values + '>'

        command_info = {
            "command": " ".join(sub_commands),
            "arguments": arguments,
            "source": RecommendationSource.Aladdin,
            "type": RecommendType.Command,
            "example": example
        }
        if "description" in recommended_item and recommended_item["description"]:
            command_info['reason'] = recommended_item["description"]
        if "score" in recommended_item and recommended_item["score"]:
            command_info['score'] = recommended_item["score"]

        result.append(command_info)

    return result
