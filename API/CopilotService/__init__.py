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

    try:
        result = []
        if service_type == ServiceType.KNOWLEDGE_SEARCH:
            result = knowledge_search(question, top_num)
            if len(result) == 0 or not pass_verification(context, question, result):
                result = []
        elif service_type == ServiceType.GPT_GENERATION:
            context.custom_context.gpt_task_name = 'GENERATE_SCENARIO'
            context.custom_context.estimated_question_tokens = num_tokens_from_message(question)
            gpt_result = gpt_generate(context, question, history)
            result = [_build_scenario_response(gpt_result)] if gpt_result else []
        elif service_type == ServiceType.MIX:
            result = knowledge_search(question, top_num)
            if len(result) == 0 or not pass_verification(question, result):
                context.custom_context.gpt_task_name = 'GENERATE_SCENARIO'
                context.custom_context.estimated_question_tokens = num_tokens_from_message(question)
                gpt_result = gpt_generate(context, question, history)
                result = [_build_scenario_response(gpt_result)] if gpt_result else []
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
