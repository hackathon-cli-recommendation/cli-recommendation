import os
import httpx
from typing import Optional
import logging
import re
from rapidfuzz import fuzz

from common.util import determine_strings_are_similar, parse_command_info

embedding_model_url = os.environ["EMBEDDING_MODEL_URL"]
chunk_sieve_top_num = int(os.environ.get("CHUNK_SIEVE_TOP_NUM", "3"))
keyword_similarity_score = float(os.environ["KEYWORD_SIMILARITY_SCORE"])


async def _embedding_text_to_vector(text):
    try:
        headers = {
            'Content-Type': 'application/json',
            'api-key': os.environ["OPENAI_API_KEY"]
        }

        payload = {
            "input": text
        }

        async with httpx.AsyncClient() as client:
            result = await client.post(embedding_model_url, json=payload, headers=headers)
            result.raise_for_status()

        data = result.json().get("data")
        if not data or not data[0].get("embedding"):
            logging.error('No embedding vector for the text %s', text)
            return []

        return data[0]["embedding"]
    except httpx.RequestError as e:
        logging.error('Error while retrieving embedding vector for the text %s: %s', text, e)
        return []


async def _retrieve_chunks_from_learn_knowledge_index_service(vector_values, filter_command=None):
    try:
        # learn knowledge index service endpoint URL
        learn_knowledge_index_url = os.environ["LEARN_KNOWLEDGE_INDEX_SERVICE_URL"]

        headers = {
            'Content-Type': 'application/json',
            'Authorization': os.environ["LEARN_KNOWLEDGE_INDEX_ACCESS_TOKEN"]
        }

        filter = "depotName eq 'Azure.azure-cli-docs'"
        if filter_command:
            filter = f"({filter}) and (title eq '{filter_command}')"

        payload = {
            "filter": filter,
            "vector":{
                "values": vector_values,
                "top": int(os.environ["RETRIEVED_NUMBER_OF_CHUNKS"])
            }
        }

        score_threshold = os.environ.get("LEARN_KNOWLEDGE_INDEX_SCORE_THRESHOLD")
        if score_threshold:
            learn_knowledge_index_url = learn_knowledge_index_url + "?scoreThreshold=" + score_threshold

        async with httpx.AsyncClient() as client:
            result = await client.post(learn_knowledge_index_url, json=payload, headers=headers)
            result.raise_for_status()
    except httpx.RequestError as e:
        logging.error('Error while retrieving chunks from learn knowledge index service: %s', e)
        return []

    return convert_chunks_to_json(result.json())


def trim_command_and_chunk_with_invalid_params(command, chunk):
    """
    Trim the incorrect parameters in command and suggest the possible correct parameters in returned chunk.
    Args:
        command: the command contains incorrect parameters
        chunk: a chunk contains all parameters related to the command
    Returns: A tuple. The first element is the command with only correct parameter.
    The second element is the chunk with possible correct parameters
    """
    chunk_copy = chunk.copy()
    cmd_sig, params = parse_command_info(command)
    cmd_params = []
    unmatched_params = []
    for param in params:
        if _pop_param_in_chunk(param, chunk_copy):
            cmd_params.append(param)
        else:
            unmatched_params.append(param)
    chunk_copy['optional parameters'] = []
    for param in unmatched_params:
        similar_params = _find_top_n_similar_params(param, chunk['optional parameters'])
        chunk_copy['optional parameters'].extend(similar_params)
    chunk_copy['optional parameters'] = _dedup_param_group(chunk_copy['optional parameters'])
    valid_cmd = cmd_sig + ' ' + ' '.join(cmd_params)
    return valid_cmd, chunk_copy


async def retrieve_chunk_for_command(command: str):
    """
    Retrieve chunk according to command signature
    Args:
        command: full command
    Returns: a merged chunk that is related to the command
    """
    sig, _ = parse_command_info(command)
    vector_values = await _embedding_text_to_vector(command)

    chunk_items = await _retrieve_chunks_from_learn_knowledge_index_service(vector_values, filter_command=sig)
    chunks = merge_chunks_by_command(chunk_items)
    return chunks[0] if chunks else None


async def retrieve_chunks_for_atomic_task(task: str):
    """
    Retrieve chunks according to task info
    Args:
        task: task description
    Returns: List of chunks that are related to the task
    """
    vector_values = await _embedding_text_to_vector(task)

    chunk_items = await _retrieve_chunks_from_learn_knowledge_index_service(vector_values)
    chunks = merge_chunks_by_command(chunk_items)
    return chunks[:chunk_sieve_top_num]


def convert_chunks_to_json(chunks_list):
    data_list = []
    for chunk in chunks_list["items"]:
        chunk2json = {}
        chunk2json["command"] = chunk["title"]
        chunk2json["summary"] = re.search(r"### Summary\n([\s\S]*?)(?=\n\n###|\Z)", chunk["content"]).group(1)
        optional_params = []
        optional_params_content = re.search(r"### Optional Parameters\n\n([\s\S]*?)(?=\n\n###|\Z)", chunk["content"])
        optional_params_content = optional_params_content.group(1) if optional_params_content else ""
        params = re.findall(r"(--[\s\S]*?)(?=\n\n--|$)", optional_params_content)
        for param in params:
            item = {}
            item["name"] = param.split("\n")[0]
            item["desc"] = param[len(item["name"])+1:]
            optional_params.append(item)
        require_params = []
        require_params_desc = re.search(r"### Required Parameters\n\n([\s\S]*?)(?=\n\n###|\Z)", chunk["content"])
        require_params_desc = require_params_desc.group(1) if require_params_desc else ""
        params = re.findall(r"(--[\s\S]*?)(?=\n\n--|$)", require_params_desc)
        for param in params:
            item = {}
            item["name"] = param.split("\n")[0]
            item["desc"] = param[len(item["name"])+1:]
            require_params.append(item)
        if optional_params:
            chunk2json["optional parameters"] = optional_params
        if require_params:
            chunk2json["required parameters"] = require_params
        chunk2json["score"] = chunk["score"]
        data_list.append(chunk2json)
    return data_list


def filter_chunks_by_keyword_similarity(chunks_list, command):
    """
    Keep only the chunks and their associated parameters that are relevant to the current command, and discard the rest.
    Args:
        chunks_list: list of chunks to be filter
        command: filter criteria
    Returns: list of chunks that have been filtered
    """
    filtered_chunks = []
    for chunk in chunks_list:
        # find chunks that match the command signature exactly
        if command.startswith(chunk['command']):
            filtered_chunks.append(filter_chunk_parameters(chunk, command))
    if filtered_chunks:
        return filtered_chunks

    command_sig = command.split(' -', 1)[0]
    for chunk in chunks_list:
        # find chunks that have a similar signature with command
        if determine_strings_are_similar(command_sig[3:], chunk['command'][3:]):
            filtered_chunks.append(filter_chunk_parameters(chunk, command))
    if filtered_chunks:
        return filtered_chunks

    return []


def filter_chunk_parameters(chunk, command):
    """
    Keep only the optional parameters that are relevant to the current command, and discard the rest.
    Args:
        chunk: a chunk with parameters to be filtered
        command:
    Returns: a new chunk with only related parameters
    """
    chunk_copy = chunk.copy()
    chunk_copy['optional parameters'] = []
    for chunk_param in chunk.get('optional parameters', []):
        if calc_param_similarity_score(chunk_param, command) >= keyword_similarity_score:
            chunk_copy['optional parameters'].append(chunk_param)
    return chunk_copy


def merge_chunks_by_command(chunks_list):
    summary_dict = {}
    for chunk in chunks_list:
        command = chunk['command']
        if command in summary_dict:
            existing_chunk = summary_dict[command]
            existing_optional_parameters = existing_chunk['optional parameters'] if 'optional parameters' in existing_chunk else []
            existing_required_parameters = existing_chunk['required parameters'] if 'required parameters' in existing_chunk else []
            new_optional_parameters = chunk['optional parameters'] if 'optional parameters' in chunk else []
            new_required_parameters = chunk['required parameters'] if 'required parameters' in chunk else []

            for param in new_optional_parameters:
                if param not in existing_optional_parameters:
                    existing_optional_parameters.append(param)

            for param in new_required_parameters:
                if param not in existing_required_parameters:
                    existing_required_parameters.append(param)

            existing_chunk['score'] = max(existing_chunk['score'], chunk['score'])
        else:
            summary_dict[command] = chunk

    merged_chunks = list(summary_dict.values())
    return merged_chunks


def _pop_param_in_chunk(param, chunk):
    for param_group in ['required parameters', 'optional parameters']:
        for idx, chunk_param in enumerate(chunk.get(param_group, [])):
            for chunk_param_option in chunk_param['name'].split():
                if param == chunk_param_option:
                    return chunk[param_group].pop(idx)
    return None


def _find_top_n_similar_params(param, chunk_param_group, top_n=3):
    params = []
    for chunk_param in chunk_param_group:
        chunk_param_copy = chunk_param.copy()
        scores = []
        # There could be several option name for a parameter, e.g. `--resource-group` and `-g`
        for chunk_option in chunk_param['name'].split():
            score = fuzz.token_sort_ratio(chunk_option, param) / 100
            scores.append(score)
        if scores and max(scores) >= keyword_similarity_score:
            chunk_param_copy['score'] = max(scores)
            params.append(chunk_param_copy)
    return sorted(params, key=lambda p: p['score'], reverse=True)[:top_n]


def _dedup_param_group(chunk_param_group):
    result = []
    param_name_set = set()
    for param in sorted(chunk_param_group, key=lambda p: p['score'], reverse=True):
        if param['name'] not in param_name_set:
            result.append(param)
            param_name_set.add(param['name'])
    return result


def calc_param_similarity_score(chunk_param, command):
    for cmd_param in [p for p in command.split() if p.startswith('-')]:
        for chunk_param_option in chunk_param['name'].split():
            score = fuzz.token_sort_ratio(chunk_param_option, cmd_param) / 100
            chunk_param['score'] = max(score, chunk_param.get('score', 0))
    return chunk_param.get('score', 0)


def get_top_chunks(chunks_list, top_num=3):
    sorted_chunks = sorted(chunks_list, key=lambda x: x['score'], reverse=True)
    return sorted_chunks[:top_num]
