import os
from typing import Optional

import requests
import json
import logging
import re

from common.util import determine_strings_are_similar, parse_command_info

embedding_model_url = os.environ["EMBEDDING_MODEL_URL"]


def _embedding_text_to_vector(text):
    try:
        headers = {
            'Content-Type': 'application/json',
            'api-key': os.environ["OPENAI_API_KEY"]
        }

        payload = {
            "input": text
        }

        result = requests.post(embedding_model_url, json.dumps(payload), headers=headers)
        result.raise_for_status()

        data = result.json().get("data")
        if not data or not data[0].get("embedding"):
            logging.error('No embedding vector for the text %s', text)
            return []

        return data[0]["embedding"]
    except requests.exceptions.RequestException as e:
        logging.error('Error while retrieving embedding vector for the text %s: %s', text, e)
        return []


def _retrieve_chunks_from_learn_knowledge_index_service(vector_values, filter_command=None):
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

    result = requests.post(learn_knowledge_index_url, json=payload, headers=headers)
    if result.status_code != 200:
        logging.error('Status:{} {} ErrorMessage:{}'.format(result.status_code, result.reason, result.text))
        return []

    return convert_chunks_to_json(result.json())


async def retrieve_chunk_for_atomic_task(task: str, command: Optional[str] = None, failure_info: Optional[str] = None):
    """
    Retrieve chunks according to task info
    Args:
        task: task description
        command: a possible incorrect command produced by GPT
        failure_info: the reason for incorrect command
    Returns: List of chunks that are related to the task
    """
    vector_values = _embedding_text_to_vector(task)

    if command and failure_info:
        if 'Unknown Command' in failure_info or 'not an Azure CLI command' in failure_info:
            chunk_items = _retrieve_chunks_from_learn_knowledge_index_service(vector_values)
        else:
            command_sig = command.split(' -', 1)[0].strip()
            chunk_items = _retrieve_chunks_from_learn_knowledge_index_service(vector_values, filter_command=command_sig)
            chunk_items = filter_chunks(chunk_items, command)
    else:
        chunk_items = _retrieve_chunks_from_learn_knowledge_index_service(vector_values)

    chunks = merge_chunks_by_command(chunk_items)
    return chunks[0] if chunks else None


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


def filter_chunks(chunks_list, command):
    filtered_chunks = []
    for chunk in chunks_list:
        if command.startswith(chunk['command']):
            filtered_chunks.append(filter_chunk_parameters(chunk, command))
    if filtered_chunks:
        return filtered_chunks

    command_sig = command.split(' -', 1)[0]
    for chunk in chunks_list:
        if determine_strings_are_similar(command_sig[3:], chunk['command'][3:]):
            filtered_chunks.append(filter_chunk_parameters(chunk, command))
    if filtered_chunks:
        return filtered_chunks

    for chunk in chunks_list:
        filtered_chunks.append(filter_chunk_parameters(chunk, command))
    return filtered_chunks


def filter_chunk_parameters(chunk, command):
    n_chunk = chunk.copy()
    n_chunk['optional parameters'] = []
    for chunk_param in chunk['optional parameters']:
        if is_param_related_to_command(chunk_param, command):
            n_chunk['optional parameters'].append(chunk_param)
    return n_chunk


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
        else:
            chunk.pop('score', None)
            summary_dict[command] = chunk

    merged_chunks = list(summary_dict.values())
    return merged_chunks


def is_param_related_to_command(chunk_param, command):
    for cmd_param in [p for p in command.split() if p.startswith('-')]:
        for chunk_param_option in chunk_param['name'].split():
            if determine_strings_are_similar(chunk_param_option, cmd_param):
                return True
    return False


def get_top_chunks(chunks_list, top_num=3):
    sorted_chunks = sorted(chunks_list, key=lambda x: x['score'], reverse=True)
    return sorted_chunks[:top_num]
