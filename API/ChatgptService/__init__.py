import json
import logging
import os

import azure.functions as func
import openai
from common.param import get_param_list, get_param_str

from .src.response import generate_response

# initialize_openai_service
# the type of the OpenAI API service
openai.api_type = "azure"
# the key of the OpenAI API service
openai.api_key = os.environ["OPENAI_API_KEY"]
# the version of the OpenAI API service
openai.api_version = os.environ["OPENAI_API_VERSION"]
# the url of the OpenAI API service
openai.api_base = os.environ["OPENAI_API_URL"]


def main(req: func.HttpRequest) -> func.HttpResponse:
    if req.method != "POST":
        return func.HttpResponse("Chatgpt Service only supports PUT request.", status_code=200)
    if req.method == "POST":
        logging.info(
            'Chatgpt Service HTTP trigger function processed a request.')
        response_data = {"content": None, "history_msg_list": None}
        # the param dict of the chatgpt service
        user_msg = get_param_str(req, "user_msg", required=True)
        history_msg = get_param_list(req, "history_msg")
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
            content = response["choices"][0]["message"]["content"]
            history_msg.append({"role": "user", "content": user_msg})
            history_msg.append({"role": "assistant", "content": content})
            response_data["content"] = json.loads(content.replace("'", '"'))
            response_data["history_msg"] = history_msg
            return func.HttpResponse(generate_response(data=response_data, status=200))
        except:
            return func.HttpResponse('There is some error from the server.', status_code=400)


def initialize_chatgpt_service_params():
    # use a dict to store the parameters of the chatgpt service
    # give initial values to the parameters
    default_msg = r"""[{"role": "system", "content": "You are an assistant who guide others to use Azure CLI and only provide advice on Azure CLI commands or command combinations. \nYou can complete the task in four steps:\n1. Parse the task that the user wants to accomplish.\n2. Determine how many commands are needed to complete the task.\n3. Confirm the resource name on request.\n4. If only one command is needed, please output an example of that command. If multiple commands are required, please output an example of a set of commands.\nWhen the user requests a random resource name, name the resource name in the format chatgpt-<resource type in lower case>-<current timestamp>.\nAll output must be in the format shown in the follow few-shot examples, Each output must contain a 'Description' property to briefly describe the function of the Script, a 'CommandSet' property containing examples and descriptions of all the commands, and a 'Reason' property detailing the function and flow of the script.\n"}, {"role": "user", "content": "How to Create an Azure Function that connects to an Azure Storage"}, {"role": "assistant", "content": "{'Description': 'Create an Azure Function that connects to an Azure Storage', 'CommandSet': [{'command': 'storage account create', 'arguments': ['--name', '--location', '--resource-group', '--sku'], 'reason': 'Create an Azure storage account in the resource group.', 'example': 'az storage account create --name $storage --location $location --resource-group $resourceGroup --sku $skuStorage'}, {'command': 'functionapp create', 'arguments': ['--name', '--resource-group', '--storage-account', '--consumption-plan-location', '--functions-version'], 'reason': 'Create a serverless function app in the resource group.', 'example': 'az functionapp create --name $functionApp --resource-group $resourceGroup --storage-account $storage --consumption-plan-location $location --functions-version $functionsVersion'}, {'command': 'storage account show-connection-string', 'arguments': ['--name', '--resource-group', '--query', '--output'], 'reason': 'Get the storage account connection string. (connstr will be used in subsequent commands).', 'example': 'az storage account show-connection-string --name $storage --resource-group $resourceGroup --query connectionString --output tsv'}, {'command': 'functionapp config appsettings set', 'arguments': ['--name', '--resource-group', '--settings'], 'reason': 'Update function app settings to connect to the storage account.', 'example': 'az functionapp config appsettings set --name $functionApp --resource-group $resourceGroup --settings StorageConStr=$connstr'}], 'Reason': 'Create an Azure Function that connects to an Azure Storage'}"}, {"role": "user", "content": "Please help me create a resource group with random resource name"}, {"role": "assistant", "content": "\"{'Description': 'Create a Resource Group', 'CommandSet': [{'command': 'resource group create', 'arguments': ['--name', '--location'], 'reason': 'Create a resource group', 'example': 'az group create --name chatgpt-resourcegroup-1682324585 --location $location'}], 'Reason': 'Create a Resource Group by defining group name and location'}"}, {"role": "user", "content": "I want to create a website with service and database"}, {"role": "assistant", "content": "{'Description': 'Connect an app to MongoDB (Cosmos DB).', 'CommandSet': [{'command': 'appservice plan create', 'arguments': ['--name', '--resource-group', '--location'], 'reason': 'Create an App Service Plan', 'example': 'az appservice plan create --name $appServicePlan --resource-group $resourceGroup --location $location'}, {'command': 'webapp create', 'arguments': ['--name', '--plan', '--resource-group'], 'reason': 'Create a Web App', 'example': 'az webapp create --name $webapp --plan $appServicePlan --resource-group $resourceGroup'}, {'command': 'cosmosdb create', 'arguments': ['--name', '--resource-group', '--kind'], 'reason': 'Create a Cosmos DB with MongoDB API', 'example': 'az cosmosdb create --name $cosmosdb --resource-group $resourceGroup --kind MongoDB'}, {'command': 'cosmosdb keys list', 'arguments': ['--name', '--resource-group', '--type', '--query', '--output'], 'reason': 'Get the MongoDB URL (connectionString will be used in subsequent commands).', 'example': 'az cosmosdb keys list --name $cosmosdb --resource-group $resourceGroup --type connection-strings --query connectionStrings[0].connectionString --output tsv'}, {'command': 'webapp config appsettings set', 'arguments': ['--name', '--resource-group', '--settings'], 'reason': 'Assign the connection string to an App Setting in the Web App', 'example': 'az webapp config appsettings set --name $webapp --resource-group $resourceGroup --settings MONGODB_URL=$connectionString'}], 'Reason': 'Connect an app to MongoDB (Cosmos DB).'}"}]"""
    chatgpt_service_params = {"engine": "GPT_4_32k", "temperature": 0.5, "max_tokens": 800,
                              "top_p": 0.95, "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
    for key, value in chatgpt_service_params.items():
        env_key = 'OPENAI_' + key.upper()
        chatgpt_service_params[key] = os.environ.get(env_key, default=value)
        if key in ["temperature", "top_p"]:
            chatgpt_service_params[key] = float(chatgpt_service_params[key])
        elif key in ["max_tokens", "frequency_penalty", "presence_penalty"]:
            chatgpt_service_params[key] = int(chatgpt_service_params[key])
    default_msg = json.loads(os.environ.get(
        "OPENAI_DEFAULT_MSG", default=default_msg))
    chatgpt_service_params["messages"] = default_msg
    return chatgpt_service_params
