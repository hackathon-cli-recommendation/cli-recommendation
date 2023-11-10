import json
import logging
import os
from json import JSONDecodeError
from typing import Any, Dict, List

import openai
import tiktoken
from common.context import log_dependency_call
from common.exception import CopilotException, GPTInvalidResultException, GPTTimeOutException
from openai.error import OpenAIError, RateLimitError, Timeout, TryAgain

logger = logging.getLogger(__name__)


# initialize_openai_service
# the type of the OpenAI API service
openai.api_type = "azure"
# the key of the OpenAI API service
openai.api_key = os.environ["OPENAI_API_KEY"]
# the version of the OpenAI API service
openai.api_version = os.environ["OPENAI_API_VERSION"]
# the url of the OpenAI API service
openai.api_base = os.environ["OPENAI_API_URL"]


@log_dependency_call("gpt generate")
def gpt_generate(context, system_msg: str, user_msg: str, history_msg: List[Dict[str, str]]) -> Dict[str, Any]:
    # the param dict of the chatgpt service
    chatgpt_service_params = initialize_chatgpt_service_params(system_msg)
    all_user_msg = []
    estimated_history_tokens = 0
    if history_msg:
        estimated_history_tokens = num_tokens_from_messages(history_msg)
        chatgpt_service_params["messages"].extend(history_msg)
        all_user_msg = [msg["content"]
                        for msg in history_msg if msg["role"] == "user"]
    all_user_msg.append(user_msg)
    chatgpt_service_params["messages"].append(
        {"role": "user", "content": "\n".join(all_user_msg)})
    
    context.custom_context.estimated_history_tokens = estimated_history_tokens
    context.custom_context.estimated_prompt_tokens = num_tokens_from_messages(chatgpt_service_params["messages"])
    _logging_gpt_call_cost(context)

    try:
        response = openai.ChatCompletion.create(**chatgpt_service_params)
        logging.info(f"The actual cost of {context.custom_context.gpt_task_name} GPT call is as follows: completion tokens = {response['usage']['completion_tokens']}, propmpt tokens = {response['usage']['prompt_tokens']}, total tokens = {response['usage']['total_tokens']}.")
    except (TryAgain, Timeout) as e:
        raise GPTTimeOutException() from e
    except RateLimitError as e:
        raise CopilotException('The OpenAI API rate limit is exceeded.') from e
    except OpenAIError as e:
        raise CopilotException('There is some error from the OpenAI.') from e
    chatCompletion = response.choices[0].message.content
    response.usage['model'] = response.model
    response = {
        "content": chatCompletion,
        "usage": response.usage
    }

    response = _add_estimated_usage(context, response)
    return response


def _logging_gpt_call_cost(context):
    gpt_task_name = context.custom_context.gpt_task_name
    estimated_question_tokens = context.custom_context.estimated_question_tokens
    estimated_task_list_tokens = getattr(context.custom_context, 'estimated_task_list_tokens', None)
    task_list_lens = getattr(context.custom_context, 'task_list_lens', None)
    estimated_usage_context_tokens = getattr(context.custom_context, 'estimated_usage_context_tokens', None)
    estimated_history_tokens = context.custom_context.estimated_history_tokens
    estimated_prompt_tokens = context.custom_context.estimated_prompt_tokens

    # logging GPT call cost
    message = f"The estimated cost of {gpt_task_name} GPT call is as follows: "
    message += f"question tokens = {estimated_question_tokens}, "
    message += f"task list tokens = {estimated_task_list_tokens}, task lens = {task_list_lens}, " if estimated_task_list_tokens else ""
    message += f"usage context tokens = {estimated_usage_context_tokens}, " if estimated_usage_context_tokens else ""
    message += f"history tokens = {estimated_history_tokens}, "
    message += f"propmpt tokens = {estimated_prompt_tokens}."
    logging.info(f"{message}")


def _add_estimated_usage(context, response):
    gpt_task_name = context.custom_context.gpt_task_name
    estimated_question_tokens = context.custom_context.estimated_question_tokens
    estimated_task_list_tokens = getattr(context.custom_context, 'estimated_task_list_tokens', None)
    task_list_lens = getattr(context.custom_context, 'task_list_lens', None)
    estimated_usage_context_tokens = getattr(context.custom_context, 'estimated_usage_context_tokens', None)
    estimated_history_tokens = context.custom_context.estimated_history_tokens
    estimated_prompt_tokens = context.custom_context.estimated_prompt_tokens

    # add usage to response
    response['usage']['gpt_task_name'] = gpt_task_name
    response['usage']['estimated_question_tokens'] = estimated_question_tokens
    if estimated_task_list_tokens:
        response['usage']['estimated_task_list_tokens'] = estimated_task_list_tokens
        del context.custom_context.estimated_task_list_tokens
    if task_list_lens:
        response['usage']['task_list_lens'] = task_list_lens
        del context.custom_context.task_list_lens
    if estimated_usage_context_tokens:
        response['usage']['estimated_usage_context_tokens'] = estimated_usage_context_tokens
        del context.custom_context.estimated_usage_context_tokens
    response['usage']['estimated_history_tokens'] = estimated_history_tokens
    response['usage']['estimated_prompt_tokens'] = estimated_prompt_tokens
    
    # Since one http request contains multiple GPT requests, 
    # and the fields we count are different each time, they must be cleared to avoid being carried into another GPT request.
    del context.custom_context.gpt_task_name
    del context.custom_context.estimated_question_tokens
    del context.custom_context.estimated_history_tokens
    del context.custom_context.estimated_prompt_tokens

    return response


def initialize_chatgpt_service_params(default_msg=None, chatgpt_service_params=None):
    # use a dict to store the parameters of the chatgpt service
    # give initial values to the parameter
    if not default_msg:
        default_msg = r"""[{"role": "system", "content": "You are an assistant who generates corresponding Azure CLI command combinations based on user question. You can complete the task based on the following steps:\n1. Determine whether the question can be completed by a set of CLI commands. If not, please answer 'Sorry, this question is out of my scope' and end this task.\n2. Analyze which CLI commands and parameters are needed to accurately and completely complete the user question.\n3. If the user question includes the usage information of related CLI commands as context, analyze this user question based on this context.\n4. Output the analysis results as JSON object. It must contain the 'scenario' property to briefly describe the function of this CLI script, a 'commandSet' property containing the command info, arguments info, examples and descriptions of all the commands, and a 'description' property to provide a more comprehensive description of the script but not too long."}, {"role": "user", "content": "How to create an Azure Function that connects to an Azure Storage?"}, {"role": "assistant", "content": "{\"scenario\": \"Create an Azure Function that connects to an Azure Storage\", \"commandSet\": [{\"command\": \"az functionapp create\", \"arguments\": [\"--name\", \"--resource-group\", \"--storage-account\", \"--consumption-plan-location\", \"--functions-version\"], \"reason\": \"Create a serverless function app in the resource group\", \"example\": \"az functionapp create --name $functionApp --resource-group $resourceGroup --storage-account $storage --consumption-plan-location $location --functions-version $functionsVersion\"}, {\"command\": \"az storage account show-connection-string\", \"arguments\": [\"--name\", \"--resource-group\", \"--query\", \"--output\"], \"reason\": \"Get the storage account connection string. (connstr will be used in subsequent commands)\", \"example\": \"az storage account show-connection-string --name $storage --resource-group $resourceGroup --query connectionString --output tsv\"}, {\"command\": \"az functionapp config appsettings set\", \"arguments\": [\"--name\", \"--resource-group\", \"--settings\"], \"reason\": \"Update function app settings to connect to the storage account\", \"example\": \"az functionapp config appsettings set --name $functionApp --resource-group $resourceGroup --settings StorageConStr=$connstr\"}], \"description\": \"Create an new Azure Function that connects to an Azure Storage by using connectionString\"}"}]"""
        default_msg = os.environ.get("OPENAI_DEFAULT_MSG", default=default_msg)
    if not chatgpt_service_params:
        chatgpt_service_params = {"engine": "GPT_4_32k", "temperature": 0.5, "max_tokens": 4000,
                              "top_p": 0.95, "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
    for key, value in chatgpt_service_params.items():
        env_key = 'OPENAI_' + key.upper()
        chatgpt_service_params[key] = os.environ.get(env_key, default=value)
        if key in ["temperature", "top_p"]:
            chatgpt_service_params[key] = float(chatgpt_service_params[key])
        elif key in ["max_tokens", "frequency_penalty", "presence_penalty"]:
            chatgpt_service_params[key] = int(chatgpt_service_params[key])
    chatgpt_service_params["messages"] = json.loads(default_msg)
    return chatgpt_service_params


def num_tokens_from_messages(messages: List[Dict[str, str]], model="gpt-3.5-turbo-0613"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo-0613":  # note: future models may deviate from this
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += -1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens
    else:
        logging.error(f"""num_tokens_from_messages() is not presently implemented for model {model}.
    See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")
        return None

def num_tokens_from_message(message: str, model="gpt-3.5-turbo-0613"):
    """Returns the number of tokens used by a messages."""
    if not isinstance(message, str):
        message = str(message)
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo-0613":  # note: future models may deviate from this
        num_tokens = len(encoding.encode(message))
        return num_tokens
    else:
        logging.error(f"""num_tokens_from_message() is not presently implemented for model {model}.
    See https://github.com/openai/openai-python/blob/main/chatml.md for information on how message is converted to tokens.""")
        return None
