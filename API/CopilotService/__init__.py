import asyncio
import json
import logging
import os
import textwrap
from enum import Enum

import azure.functions as func
from cli_validator.result import CommandSource

from common.auth import get_auth_token_for_learn_knowlegde_index, verify_token
from common.correct import correct_scenario
from common.exception import CopilotException, GPTInvalidResultException, ParameterException
from common.prompt import DEFAULT_GENERATE_SCENARIO_MSG, DEFAULT_SPLIT_TASK_MSG, DEFAULT_FIND_SIMILAR_MSG
from common.service_impl.chatgpt import gpt_generate, num_tokens_from_message
from common.service_impl.knowledge_base import knowledge_search, pass_verification
from common.service_impl.learn_knowledge_index import retrieve_chunks_for_atomic_task, filter_chunks_by_keyword_similarity, \
    merge_chunks_by_command, retrieve_chunk_for_command, trim_command_and_chunk_with_invalid_params
from common.telemetry import telemetry
from common.util import get_param_str, get_param_int, get_param_enum, get_param, generate_response

from common import validate_command_in_task

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

    system_msg = os.environ.get("OPENAI_GENERATE_SCENARIO_MSG", default=DEFAULT_GENERATE_SCENARIO_MSG)

    try:
        result = []
        if service_type == ServiceType.KNOWLEDGE_SEARCH:
            result = knowledge_search(question, top_num)
            if len(result) == 0 or not pass_verification(context, question, result):
                result = []

            return func.HttpResponse(generate_response(result, 200))

        if os.environ.get('ENABLE_RETRIEVAL_AUGMENTED_GENERATION', "true").lower() == "true":
            task_list, usage_context = asyncio.run(_retrieve_context_from_learn_knowledge_index(context, question))
            question = _add_context_to_question(context, question, task_list, usage_context)

        if service_type == ServiceType.GPT_GENERATION:
            context.custom_context.gpt_task_name = 'GENERATE_SCENARIO'
            context.custom_context.estimated_question_tokens = num_tokens_from_message(question)
            gpt_result = gpt_generate(context, system_msg, question, history)
            result = [_build_scenario_response(gpt_result)] if gpt_result else []

        elif service_type == ServiceType.MIX:
            result = knowledge_search(question, top_num)

            if len(result) == 0 or not pass_verification(context, question, result):
                context.custom_context.gpt_task_name = 'GENERATE_SCENARIO'
                context.custom_context.estimated_question_tokens = num_tokens_from_message(question)
                gpt_result = gpt_generate(context, system_msg, question, history)
                result = [_build_scenario_response(gpt_result)] if gpt_result else []

        result = [correct_scenario(s) for s in result]
    except CopilotException as e:
        logger.error(f'Response Status 500: CopilotException: {e.msg}')
        return func.HttpResponse(e.msg, status_code=500)
    return func.HttpResponse(generate_response(result, 200))


async def _retrieve_context_from_learn_knowledge_index(context, question):
    result = await _retrieve_context_for_atomic_question(context, question)
    if result is not None:
        return result

    system_msg = os.environ.get("OPENAI_SPLIT_TASK_MSG", default=DEFAULT_SPLIT_TASK_MSG)
    context.custom_context.gpt_task_name = 'SPLIT_TASK'
    context.custom_context.estimated_question_tokens = num_tokens_from_message(question)
    generate_results = gpt_generate(context, system_msg, question, history_msg=[])
    try:
        raw_task_list = _build_scenario_response(generate_results)
    except Exception as e:
        logger.error(f"Error while parsing the generate results: {generate_results}, {e}")
        return None, None

    token = get_auth_token_for_learn_knowlegde_index()

    context_tasks = [asyncio.create_task(_build_task_context(raw_task, token)) for raw_task in raw_task_list]

    context_info_list = await asyncio.gather(*context_tasks)
    task_list = [context_info[0] for context_info in context_info_list]
    chunk_list = _join_chunks_in_context(context_info_list)

    chunk_list = merge_chunks_by_command(chunk_list)
    # TODO The logic of filtering, ranking, and aggregating chunks

    return task_list, chunk_list


async def _retrieve_context_for_atomic_question(context, question):
    chunks = await retrieve_chunks_for_atomic_task(question)
    if len(chunks) == 0:
        return None
    relevant_chunk = _find_most_relevant_command_chunk(context, question, chunks)
    if relevant_chunk is None:
        return None
    return [relevant_chunk['command']], relevant_chunk


async def _build_task_context(raw_task, token):
    """
    Build a guide step and context command from a raw task
    Args:
        raw_task: the raw task generated by GPT(prompt for splitting task)
    Returns: A tuple. The first element is the guide step in str and
    the second element is a list of chunks that contain some possible commands to use.
    """
    desc = raw_task.split("||")[0]
    if len(raw_task.split("||")) > 1:
        # If GPT provides a command when splitting task, validate the command.
        cmd = raw_task.split("||")[1]
        validate_result = validate_command_in_task(cmd)
        if validate_result.is_valid and validate_result.cmd_source == CommandSource.CORE_MODULE:
            # If the GPT-provided command is valid, use it as a guide step.
            task = cmd
            chunks = []
        elif validate_result.error_message and 'not an Azure CLI command' in validate_result.error_message:
            # If GPT generates a non-CLI command, like `git clone`
            task = desc
            chunks = []
        elif validate_result.error_message and 'Unknown Command' in validate_result.error_message:
            # If the GPT-provided command has an error in command signature,
            # retrieve context chunks according to the command signature
            # because hallucination command signatures preserve the semantics of operations without attention issues,
            # and there are always only subtle differences between the hallucination and correct command signatures.
            task = desc
            chunks = await retrieve_chunks_for_atomic_task(cmd, token)
            chunks = filter_chunks_by_keyword_similarity(chunks, cmd)
        else:
            # If the GPT-provided command has a correct signature but incorrect parameters,
            # Or if the command is in extension
            # keep all correct parameters in guide step and suggest the possible correct parameters in the context chunk
            chunk = await retrieve_chunk_for_command(cmd, token)
            if chunk:
                task, chunk = trim_command_and_chunk_with_invalid_params(cmd, chunk)
                chunks = [chunk]
            else:
                # The case is rare. If the GPT-provided command is not in the learn knowledge index,
                # retrieve context chunks according to the description
                task = desc
                chunks = await retrieve_chunks_for_atomic_task(desc, token)
                chunks = filter_chunks_by_keyword_similarity(chunks, cmd)
    else:
        task = desc
        chunks = await retrieve_chunks_for_atomic_task(desc, token)
    return task, chunks


def _find_most_relevant_command_chunk(context, question, chunks):
    system_msg = os.environ.get("OPENAI_FIND_SIMILAR_MSG", default=DEFAULT_FIND_SIMILAR_MSG)
    relevant_question = textwrap.dedent(
        """\
        text A: "{}"
        text set B: {}
        """.format(question, " ".join([f'"{chunk["summary"]}"' for chunk in chunks]))
    )
    context.custom_context.gpt_task_name = 'FIND_SIMILAR'
    context.custom_context.estimated_question_tokens = num_tokens_from_message(question)
    relevant_result: str = gpt_generate(context, system_msg, relevant_question, history_msg=[])
    parts = relevant_result.rsplit('||', 1)
    if len(parts) == 2:
        chunk_desc, score = parts
        chunk_desc = chunk_desc.strip('"')
        if int(score) >= int(os.environ.get("RELEVANT_SCORE_THRESHOLD", "8")):
            try:
                idx = [chunk["summary"] for chunk in chunks].index(chunk_desc)
                return chunks[idx]
            except ValueError:
                return None
    return None


def _add_context_to_question(context, question, task_list, usage_context):
    context.custom_context.estimated_question_tokens = num_tokens_from_message(question)
    context.custom_context.task_list_lens = len(task_list)
    context.custom_context.estimated_task_list_tokens = num_tokens_from_message(task_list)
    context.custom_context.estimated_usage_context_tokens = num_tokens_from_message(usage_context)
    if task_list:
        guiding_steps_separation = "\nHere are the steps you can refer to for this question:\n"
        question = question + guiding_steps_separation + str(task_list) + '\n'
    if usage_context:
        commands_info_separation = "\nBelow are some potentially relevant CLI commands information as context, please select the commands information that may be used in the scenario of the question from context, and supplement the missing commands information of context\n"
        question = question + commands_info_separation + str(usage_context)
    return question


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


def _join_chunks_in_context(context_info_list):
    return [chunk for context_info in context_info_list for chunk in context_info[1]]
