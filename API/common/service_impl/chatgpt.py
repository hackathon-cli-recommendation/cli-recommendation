import os
from typing import Any, Dict, List
import json
import openai
from openai.error import TryAgain, Timeout, OpenAIError, RateLimitError
import logging

from common.exception import CopilotException, GPTTimeOutException, GPTInvalidResultException
from json import JSONDecodeError


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


def gpt_generate(user_msg: str, history_msg: List[Dict[str, str]]) -> Dict[str, Any]:
    # the param dict of the chatgpt service
    chatgpt_service_params = initialize_chatgpt_service_params()
    all_user_msg = []
    if history_msg:
        chatgpt_service_params["messages"].extend(history_msg)
        all_user_msg = [msg["content"]
                        for msg in history_msg if msg["role"] == "user"]
    all_user_msg.append(user_msg)
    chatgpt_service_params["messages"].append(
        {"role": "user", "content": "\n".join(all_user_msg)})
    try:
        response = openai.ChatCompletion.create(**chatgpt_service_params)
    except (TryAgain, Timeout) as e:
        raise GPTTimeOutException() from e
    except RateLimitError as e:
        raise CopilotException('The OpenAI API rate limit is exceeded.') from e
    except OpenAIError as e:
        raise CopilotException('There is some error from the OpenAI.') from e
    content = response["choices"][0]["message"]["content"]
    if content and content[0].isalpha() and ('sorry' in content.lower() or 'apolog' in content.lower()):
        logger.info(f"OpenAI Apology Output: {content}")
        return None
    try:
        # If only single quotes exist, replace them with double quotes.
        if "'" in content and not '"' in content:
            content = json.loads(content.replace("'", '"'))
        # In other cases, convert directly to json
        else:
            content = json.loads(content)
        return content
    except JSONDecodeError as e:
        logger.error(f"JSONDecodeError: {content}")
        raise GPTInvalidResultException from e


def initialize_chatgpt_service_params(default_msg=None, chatgpt_service_params=None):
    # use a dict to store the parameters of the chatgpt service
    # give initial values to the parameter
    if not default_msg:
        default_msg = r"""[{"role": "system", "content": "You are an assistant who generates corresponding Azure CLI command combinations based on user question. You can complete the task based on the following steps:\n1. Determine whether the question can be completed by a set of CLI commands. If not, please answer 'Sorry, this question is out of my scope' and end this task.\n2. Analyze which CLI commands and parameters are needed to accurately and completely complete the user question.\n3. If the user question includes the usage information of related CLI commands as context, analyze this user question based on this context.\n4. Output the analysis results as JSON object. It must contain the 'scenario' property to briefly describe the function of this CLI script, a 'commandSet' property containing the command info, arguments info, examples and descriptions of all the commands, and a 'description' property to provide a more comprehensive description of the script but not too long."}, {"role": "user", "content": "How to create an Azure Function that connects to an Azure Storage?"}, {"role": "assistant", "content": "{\"scenario\": \"Create an Azure Function that connects to an Azure Storage\", \"commandSet\": [{\"command\": \"az functionapp create\", \"arguments\": [\"--name\", \"--resource-group\", \"--storage-account\", \"--consumption-plan-location\", \"--functions-version\"], \"reason\": \"Create a serverless function app in the resource group\", \"example\": \"az functionapp create --name $functionApp --resource-group $resourceGroup --storage-account $storage --consumption-plan-location $location --functions-version $functionsVersion\"}, {\"command\": \"az storage account show-connection-string\", \"arguments\": [\"--name\", \"--resource-group\", \"--query\", \"--output\"], \"reason\": \"Get the storage account connection string. (connstr will be used in subsequent commands)\", \"example\": \"az storage account show-connection-string --name $storage --resource-group $resourceGroup --query connectionString --output tsv\"}, {\"command\": \"az functionapp config appsettings set\", \"arguments\": [\"--name\", \"--resource-group\", \"--settings\"], \"reason\": \"Update function app settings to connect to the storage account\", \"example\": \"az functionapp config appsettings set --name $functionApp --resource-group $resourceGroup --settings StorageConStr=$connstr\"}], \"description\": \"Create an new Azure Function that connects to an Azure Storage by using connectionString\"}"}]"""
        default_msg = json.loads(os.environ.get(
            "OPENAI_DEFAULT_MSG", default=default_msg))
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
    chatgpt_service_params["messages"] = default_msg
    return chatgpt_service_params
