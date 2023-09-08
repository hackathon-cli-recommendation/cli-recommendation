import os
from enum import Enum
import azure.functions as func

from common.exception import ParameterException, CopilotException
from common.service_impl.chatgpt import gpt_generate
from common.service_impl.knowledge import knowledge_search
from common.util import get_param_str, get_param_int, get_param_enum, get_param, generate_response


class ServiceType(str, Enum):
    MIX = 'Mix'
    KNOWLEDGE_SEARCH = 'knowledgeSearch'
    GPT_GENERATION = 'GPTGeneration'


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        question = get_param_str(req, 'question', required=True)
        history = get_param(req, 'history', default=[])
        top_num = get_param_int(req, 'top_num', default=5)
        service_type = get_param_enum(req, 'type', ServiceType, default=ServiceType.MIX)
    except ParameterException as e:
        return func.HttpResponse(e.msg, status_code=400)

    try:
        result = []
        if service_type == ServiceType.KNOWLEDGE_SEARCH:
            result = knowledge_search(question, top_num)
            if len(result) > 0 and result[0]['score'] < float(os.environ.get('KNOWLEDGE_QUALITY_THRESHOLD', "1.0")):
                print(f"Knowledge quality is too low, score: {result[0]['score']}")
                result = []
            elif len(result) == 0:
                print("No knowledge found")
        elif service_type == ServiceType.GPT_GENERATION:
            result = [gpt_generate(question, history)]
        elif service_type == ServiceType.MIX:
            result = knowledge_search(question, top_num)
            if len(result) == 0 or result[0]['score'] < float(os.environ.get('KNOWLEDGE_QUALITY_THRESHOLD', "1.0")):
                result = [gpt_generate(question, history)]
    except CopilotException as e:
        return func.HttpResponse(e.msg, status_code=400)
    return func.HttpResponse(generate_response(result, 200))
