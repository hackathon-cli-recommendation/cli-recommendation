import json
import logging
import os
from enum import Enum
from json import JSONDecodeError

import azure.functions as func
from common.auth import verify_token
from common.correct import correct_scenario
from common.exception import CopilotException, GPTInvalidResultException, ParameterException
from common.service_impl.chatgpt import gpt_generate, num_tokens_from_message
from common.service_impl.knowledge import knowledge_search, pass_verification
from common.telemetry import telemetry
from common.util import generate_response, get_param, get_param_enum, get_param_int, get_param_str

logger = logging.getLogger(__name__)
DEFAULT_GENERATE_SCENARIO_MSG = r"""[{"role": "system", "content": "You are an assistant who generates corresponding Azure CLI command combinations based on user question. You can complete the task based on the following steps:\n1. Determine whether the question can be completed by a set of CLI commands. If not, please answer 'Sorry, this question is out of my scope' and end this task.\n2. Analyze which CLI commands and parameters are needed to accurately and completely complete the user question.\n3. If the user question includes the usage information of related CLI commands as context, analyze this user question based on this context.\n4. Output the analysis results as JSON object. It must contain the 'scenario' property to briefly describe the function of this CLI script, a 'commandSet' property containing the command info, arguments info, examples and descriptions of all the commands, and a 'description' property to provide a more comprehensive description of the script but not too long."}, {"role": "user", "content": "How to create an Azure Function that connects to an Azure Storage?"}, {"role": "assistant", "content": "{\"scenario\": \"Create an Azure Function that connects to an Azure Storage\", \"commandSet\": [{\"command\": \"az functionapp create\", \"arguments\": [\"--name\", \"--resource-group\", \"--storage-account\", \"--consumption-plan-location\", \"--functions-version\"], \"reason\": \"Create a serverless function app in the resource group\", \"example\": \"az functionapp create --name $functionApp --resource-group $resourceGroup --storage-account $storage --consumption-plan-location $location --functions-version $functionsVersion\"}, {\"command\": \"az storage account show-connection-string\", \"arguments\": [\"--name\", \"--resource-group\", \"--query\", \"--output\"], \"reason\": \"Get the storage account connection string. (connstr will be used in subsequent commands)\", \"example\": \"az storage account show-connection-string --name $storage --resource-group $resourceGroup --query connectionString --output tsv\"}, {\"command\": \"az functionapp config appsettings set\", \"arguments\": [\"--name\", \"--resource-group\", \"--settings\"], \"reason\": \"Update function app settings to connect to the storage account\", \"example\": \"az functionapp config appsettings set --name $functionApp --resource-group $resourceGroup --settings StorageConStr=$connstr\"}], \"description\": \"Create an new Azure Function that connects to an Azure Storage by using connectionString\"}"}]"""


class ServiceType(str, Enum):
    MIX = 'Mix'
    KNOWLEDGE_SEARCH = 'knowledgeSearch'
    GPT_GENERATION = 'GPTGeneration'


@telemetry
@verify_token
def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    try:
        question = get_param_str(req, 'question', required=True)
        history = get_param(req, 'history', default=[])
        top_num = get_param_int(req, 'top_num', default=5)
        service_type = get_param_enum(req, 'type', ServiceType, default=os.environ.get("DEFAULT_SERVICE_TYPE", ServiceType.GPT_GENERATION))
    except ParameterException as e:
        logger.error(f'Response Status 400: ParameterException: {e.msg}')
        return func.HttpResponse(e.msg, status_code=400)

    system_msg = os.environ.get("OPENAI_DEFAULT_MSG", default=DEFAULT_GENERATE_SCENARIO_MSG)
    try:
        result = []
        if service_type == ServiceType.KNOWLEDGE_SEARCH:
            result = knowledge_search(question, top_num)
            if len(result) == 0 or not pass_verification(context, question, result):
                result = []
        elif service_type == ServiceType.GPT_GENERATION:
            context.custom_context.gpt_task_name = 'GENERATE_SCENARIO'
            context.custom_context.estimated_question_tokens = num_tokens_from_message(question)
            gpt_result = gpt_generate(context, system_msg, question, history)
            result = _build_scenario_response(gpt_result)
            result = [result] if result else []
        elif service_type == ServiceType.MIX:
            result = knowledge_search(question, top_num)
            if len(result) == 0 or not pass_verification(context, question, result):
                context.custom_context.gpt_task_name = 'GENERATE_SCENARIO'
                context.custom_context.estimated_question_tokens = num_tokens_from_message(question)
                gpt_result = gpt_generate(context, system_msg, question, history)
                result = _build_scenario_response(gpt_result)
                result = [result] if result else []
        result = [correct_scenario(s) for s in result]
    except CopilotException as e:
        logger.error(f'Response Status 500: CopilotException: {e.msg}')
        return func.HttpResponse(e.msg, status_code=500)
    return func.HttpResponse(generate_response(result, 200))


def _build_scenario_response(content):
    if not content: 
        return None
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
