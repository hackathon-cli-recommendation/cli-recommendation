import logging
import os
from enum import Enum
import azure.functions as func

from common.correct import correct_scenario
from common.exception import ParameterException, CopilotException
from common.service_impl.chatgpt import gpt_generate
from common.service_impl.knowledge import knowledge_search, pass_verification
from common.util import get_param_str, get_param_int, get_param_enum, get_param, generate_response, verify_token


logger = logging.getLogger(__name__)


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

    try:
        result = []
        if service_type == ServiceType.KNOWLEDGE_SEARCH:
            result = knowledge_search(question, top_num)
            if len(result) > 0 and not pass_verification(question, result):
                logger.info(f"Knowledge quality is too low, question: {question}, score: {result[0]['score']}")
                result = []
            elif len(result) == 0:
                logger.info("No knowledge found")
        elif service_type == ServiceType.GPT_GENERATION:
            answer = gpt_generate(question, history)
            result = [answer] if answer else []
        elif service_type == ServiceType.MIX:
            result = knowledge_search(question, top_num)
            if len(result) == 0 or not pass_verification(question, result):
                answer = gpt_generate(question, history)
                result = [answer] if answer else []
    except CopilotException as e:
        logger.error(f'Response Status 500: CopilotException: {e.msg}')
        return func.HttpResponse(e.msg, status_code=500)
    return func.HttpResponse(generate_response(result, 200))
