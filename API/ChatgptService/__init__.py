import logging
import os
import openai
import json
import azure.functions as func

from .src.util import get_param_str
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
    logging.info('Chatgpt Service HTTP trigger function processed a request.')
    response_data = {"content": None, "history_msg_list": None}
    # the param dict of the chatgpt service
    user_msg = get_param_str(req, "user_msg", required=True)
    history_msg_list = get_param_str(req, "history_msg")
    chatgpt_service_params = initialize_chatgpt_service_params()
    if history_msg_list:
        chatgpt_service_params["messages"].extend(history_msg_list)
    chatgpt_service_params["messages"].append(
        {"role": "user", "content": user_msg})
    try:
        response = openai.ChatCompletion.create(**chatgpt_service_params)
        content = response["choices"][0]["content"]
        history_msg_list.append({"role": "user", "content": user_msg})
        history_msg_list.append({"role": "assistant", "content": content})
        response_data["content"] = content
        response_data["history_msg_list"] = history_msg_list
        return func.HttpResponse(generate_response(data=response_data, status=200))
    except:
        return func.HttpResponse('There is some error from the server.', status_code=400)


def initialize_chatgpt_service_params():
    # use a dict to store the parameters of the chatgpt service
    # give initial values to the parameters
    default_msg = [{"role": "system", "content": "You are an assistant who guide others to use Azure CLI and only provide advice on Azure CLI commands or command combinations. \n\nYou can complete the task in three steps:\n1. Parse the task that the user wants to accomplish\n2. Determine how many commands are needed to complete the task\n3. If only one command is needed, please output an example of that command. If multiple commands are required, please output an example of a set of commands.\n \nPlease note that all output formats must follow few-shot examples, do not output any other opening remarks, closing remarks, explanation and pattern."},
                   {"role": "user", "content": "I want to create a VM"},
                   {"role": "assistant",
                       "content": "az vm create -n <resource_name> -g <resource_group> --image <image>"},
                   {"role": "user", "content": "I want to create a website with service and database"},
                   {"role": "assistant",
                       "content": "// Create an App Service Plan\naz appservice plan create --name <plan_name> --resource-group <resource_group> --location <location>\n// Create a Web App\naz webapp create --name <webapp_name> --plan <plan_name> --resource-group <resource_group>\n// Create a Cosmos DB with MongoDB API\naz cosmosdb create --name <cosmosdb_name> --resource-group <resource_group> --kind <account_type>\n// Get the MongoDB URL (connectionString will be used in subsequent commands)\naz cosmosdb keys list --name <cosmosdb_name> --resource-group <resource_group> --type <account_key_type>\n// Assign the connection string to an App Setting in the Web App\naz webapp config appsettings set --name <webapp_name> --resource-group <resource_grpup> --settings <connect_string>"},
                   {"role": "user", "content": "How to create a VM"},
                   {"role": "assistant", "content": "az vm create -n <resource_name> -g <resource_group> --image <image>"}]

    chatgpt_service_params = {"engine": "GPT_4_32k", "temperature": 0.5, "max_tokens": 800,
                              "top_p": 0.95, "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
    # if os.environ[] not None
    for key in chatgpt_service_params.keys():
        if os.environ["OPENAI_" + key.upper()] is not None:
            chatgpt_service_params[key] = os.environ["OPENAI_" + key.upper()]
    chatgpt_service_params["messages"] = default_msg
    return chatgpt_service_params


def generate_response(data, status, error=None):
    response_data = {
        'data': data,
        'error': error,
        'status': status,
        # The version of the API, which is defined in the function app settings and can be changed without redeploying the whole function.
        'api_version': os.environ["API_Version"]
    }
    return json.dumps(response_data)
