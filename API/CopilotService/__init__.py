import logging
import os
from enum import Enum
import asyncio
import json
import azure.functions as func

from common.exception import ParameterException, CopilotException, GPTInvalidResultException
from common.service_impl.chatgpt import gpt_generate, num_tokens_from_message
from common.service_impl.knowledge_base import knowledge_search, pass_verification
from common.service_impl.learn_knowledge_index import retrieve_chunks_for_atomic_task
from common.util import get_param_str, get_param_int, get_param_enum, get_param, generate_response
from common.auth import verify_token, get_auth_token_for_learn_knowlegde_index
from json import JSONDecodeError


logger = logging.getLogger(__name__)


DEFAULT_GENERATE_SCENARIO_MSG = r"""[{"role": "system", "content": "You are an assistant who guide others to use Azure CLI and only provide advice on Azure CLI commands or command combinations. \nYou can complete the task in four steps:\n1. Parse the task that the user wants to accomplish.\n2. Determine how many commands are needed to complete the task.\n3. Confirm the resource name on request.\n4. If only one command is needed, please output an example of that command. If multiple commands are required, please output an example of a set of commands.\nWhen the user requests a random resource name, name the resource name in the format chatgpt-<resource type in lower case>-<current timestamp>.\nAll output must be in the format shown in the follow few-shot examples, Each output must contain a 'Description' property to briefly describe the function of the Script, a 'CommandSet' property containing examples and descriptions of all the commands, and a 'Reason' property detailing the function and flow of the script.\n"}, {"role": "user", "content": "How to Create an Azure Function that connects to an Azure Storage"}, {"role": "assistant", "content": "{'Description': 'Create an Azure Function that connects to an Azure Storage', 'CommandSet': [{'command': 'storage account create', 'arguments': ['--name', '--location', '--resource-group', '--sku'], 'reason': 'Create an Azure storage account in the resource group.', 'example': 'az storage account create --name $storage --location $location --resource-group $resourceGroup --sku $skuStorage'}, {'command': 'functionapp create', 'arguments': ['--name', '--resource-group', '--storage-account', '--consumption-plan-location', '--functions-version'], 'reason': 'Create a serverless function app in the resource group.', 'example': 'az functionapp create --name $functionApp --resource-group $resourceGroup --storage-account $storage --consumption-plan-location $location --functions-version $functionsVersion'}, {'command': 'storage account show-connection-string', 'arguments': ['--name', '--resource-group', '--query', '--output'], 'reason': 'Get the storage account connection string. (connstr will be used in subsequent commands).', 'example': 'az storage account show-connection-string --name $storage --resource-group $resourceGroup --query connectionString --output tsv'}, {'command': 'functionapp config appsettings set', 'arguments': ['--name', '--resource-group', '--settings'], 'reason': 'Update function app settings to connect to the storage account.', 'example': 'az functionapp config appsettings set --name $functionApp --resource-group $resourceGroup --settings StorageConStr=$connstr'}], 'Reason': 'Create an Azure Function that connects to an Azure Storage'}"}, {"role": "user", "content": "Please help me create a resource group with random resource name"}, {"role": "assistant", "content": "\"{'Description': 'Create a Resource Group', 'CommandSet': [{'command': 'resource group create', 'arguments': ['--name', '--location'], 'reason': 'Create a resource group', 'example': 'az group create --name chatgpt-resourcegroup-1682324585 --location $location'}], 'Reason': 'Create a Resource Group by defining group name and location'}"}, {"role": "user", "content": "I want to create a website with service and database"}, {"role": "assistant", "content": "{'Description': 'Connect an app to MongoDB (Cosmos DB).', 'CommandSet': [{'command': 'appservice plan create', 'arguments': ['--name', '--resource-group', '--location'], 'reason': 'Create an App Service Plan', 'example': 'az appservice plan create --name $appServicePlan --resource-group $resourceGroup --location $location'}, {'command': 'webapp create', 'arguments': ['--name', '--plan', '--resource-group'], 'reason': 'Create a Web App', 'example': 'az webapp create --name $webapp --plan $appServicePlan --resource-group $resourceGroup'}, {'command': 'cosmosdb create', 'arguments': ['--name', '--resource-group', '--kind'], 'reason': 'Create a Cosmos DB with MongoDB API', 'example': 'az cosmosdb create --name $cosmosdb --resource-group $resourceGroup --kind MongoDB'}, {'command': 'cosmosdb keys list', 'arguments': ['--name', '--resource-group', '--type', '--query', '--output'], 'reason': 'Get the MongoDB URL (connectionString will be used in subsequent commands).', 'example': 'az cosmosdb keys list --name $cosmosdb --resource-group $resourceGroup --type connection-strings --query connectionStrings[0].connectionString --output tsv'}, {'command': 'webapp config appsettings set', 'arguments': ['--name', '--resource-group', '--settings'], 'reason': 'Assign the connection string to an App Setting in the Web App', 'example': 'az webapp config appsettings set --name $webapp --resource-group $resourceGroup --settings MONGODB_URL=$connectionString'}], 'Reason': 'Connect an app to MongoDB (Cosmos DB).'}"}]"""
DEFAULT_SPLIT_TASK_MSG = r"""[{"role": "system", "content": "You are an assistant who breaks down user question into multiple corresponding step description and Azure CLI commands. You can complete the task based on the following steps:\n1. Determine whether the question can be completed by a set of Azure CLI commands. If not, please output empty array [] and end this task.\n2. Analyze the steps related to Azure CLI commands in this question and confirm each step must correspond to a single Azure CLI command.\n3. Output corresponding descriptions for each step without meaningless conjunctions. If a step can be completed by using an Azure CLI command that you know, output the corresponding command and parameters info of this step after the step description. Use \"||\" as a separator between step and command information.\n4. Ignore the step which contains general Azure CLI commands unrelated to specific scenarios in the question (such as 'az group create', 'az login').\n5. Ignore the step which contains non Azure CLI commands that do not start with \"az\" (such as docker, bash and kubectl commads).\n6. Ignore the step which contains the description unrelated to Azure CLI commands.\n7. If this question is too complex and requires many steps to be split, then only retain up to 8 of the most core steps.\nFinally, output the results as a JSON array."}, {"role": "user", "content": "How to create an Azure Function that connects to an Qumulo Storage?"}, {"role": "assistant", "content": "['Create an Azure Function app||az functionapp create --name --resource-group --storage-account --consumption-plan-location --functions-version', 'Create a Qumulo Storage account', 'Show a connection string for storage account||az storage account show-connection-string --name --resource-group --query --output', 'Add connection string to Azure Function settings||az functionapp config appsettings set --name --resource-group --settings']"}]"""


class ServiceType(str, Enum):
    MIX = 'Mix'
    KNOWLEDGE_SEARCH = 'knowledgeSearch'
    GPT_GENERATION = 'GPTGeneration'


@verify_token
def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        question = get_param_str(req, 'question', required=True)
        history = get_param(req, 'history', default=[])
        top_num = get_param_int(req, 'top_num', default=5)
        service_type = get_param_enum(req, 'type', ServiceType, default=os.environ.get("DEFAULT_SERVICE_TYPE", ServiceType.GPT_GENERATION))
    except ParameterException as e:
        logger.error(f'Response Status 400: ParameterException: {e.msg}')
        return func.HttpResponse(e.msg, status_code=400)

    system_msg = os.environ.get("OPENAI_GENERATE_SCENARIO_MSG", default=DEFAULT_GENERATE_SCENARIO_MSG)

    try:
        result = []
        if service_type == ServiceType.KNOWLEDGE_SEARCH:
            result = knowledge_search(question, top_num)
            if len(result) == 0 or not pass_verification(question, result):
                result = []

            return func.HttpResponse(generate_response(result, 200))

        if os.environ.get('ENABLE_RETRIEVAL_AUGMENTED_GENERATION', "true").lower() == "true":
            task_list, usage_context = asyncio.run(_retrieve_context_from_learn_knowledge_index(question))
            question, num_tokens = _add_context_to_queston(question, task_list, usage_context)

        if service_type == ServiceType.GPT_GENERATION:
            num_tokens['gpt_task_name'] = 'GENERATE_SCENARIO'
            gpt_result = gpt_generate(system_msg, question, history, **num_tokens)
            result = [_build_scenario_response(gpt_result)] if gpt_result else []
    
        elif service_type == ServiceType.MIX:
            result = knowledge_search(question, top_num)

            if len(result) == 0 or not pass_verification(question, result):
                num_tokens['gpt_task_name'] = 'GENERATE_SCENARIO'
                gpt_result = gpt_generate(system_msg, question, history, **num_tokens)
                result = [_build_scenario_response(gpt_result)] if gpt_result else []

    except CopilotException as e:
        logger.error(f'Response Status 500: CopilotException: {e.msg}')
        return func.HttpResponse(e.msg, status_code=500)
    return func.HttpResponse(generate_response(result, 200))


async def _retrieve_context_from_learn_knowledge_index(question):
    system_msg = os.environ.get("OPENAI_SPLIT_TASK_MSG", default=DEFAULT_SPLIT_TASK_MSG)
    num_tokens = {
        "question_tokens": num_tokens_from_message(question),
        "gpt_task_name": 'SPLIT_TASK'
    }
    generate_results = gpt_generate(system_msg, question, history_msg=[], **num_tokens)
    try:
        task_list = _build_scenario_response(generate_results)
    except Exception as e:
        logger.error(f"Error while parsing the generate results: {generate_results}, {e}")

    token = get_auth_token_for_learn_knowlegde_index()

    splited_tasks = []
    for task_info in task_list:
        # use task command as task info when length of task info > 1, otherwise use task desc as task info
        task_info = task_info.split("||")
        task_info = task_info[1] if len(task_info) > 1 else task_info[0]
        splited_tasks.append(asyncio.create_task(retrieve_chunks_for_atomic_task(task_info, token)))

    chunks_list = []
    if len(splited_tasks) > 0:
        chunks_list = await asyncio.gather(*splited_tasks)

    # TODO The logic of filtering, ranking, and aggregating chunks

    return task_list, chunks_list


def _add_context_to_queston(question, task_list, usage_context):
    num_tokens = {
        "question_tokens": num_tokens_from_message(question),
        "task_list_lens": len(task_list),
        "task_list_tokens": num_tokens_from_message(task_list),
        "usage_tokens": num_tokens_from_message(usage_context),
    }
    if task_list:
        guiding_steps_separation = "\nHere are the steps you can refer to for this question:\n"
        question = question + guiding_steps_separation + str(task_list) + '\n'
    if task_list:
        commands_info_separation = "\nBelow are some potentially relevant CLI commands information as context, please select the commands information that may be used in the scenario of the question from context, and supplement the missing commands information of context\n"
        question = question + commands_info_separation + str(usage_context)
    return question, num_tokens


def _build_scenario_response(content):

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
