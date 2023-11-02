import os
import httpx
import logging
import re

from common.auth import get_auth_token_for_learn_knowlegde_index
from common.util import determine_strings_are_similar, parse_command_info

embedding_model_url = os.environ["EMBEDDING_MODEL_URL"]


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


async def _retrieve_chunks_from_learn_knowledge_index_service(vector_values, filter_command=None, token=None):
    try:
        # learn knowledge index service endpoint URL  
        learn_knowledge_index_url = os.environ["LEARN_KNOWLEDGE_INDEX_SERVICE_URL"]

        headers = {
            'Content-Type': 'application/json',
            'Authorization': os.environ["LEARN_KNOWLEDGE_INDEX_ACCESS_TOKEN"] if not token else token
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


async def retrieve_chunks_for_atomic_task(task_info, token=None):
    vector_values = await _embedding_text_to_vector(task_info)

    is_command = task_info.startswith("az ")
    if is_command:
        command_info, parameters_info = parse_command_info(task_info)
        chunk_items = await _retrieve_chunks_from_learn_knowledge_index_service(vector_values, filter_command=command_info, token=token)
        # If the split subtask is a correct command, then accurately search for chunks related to this command
        if chunk_items:
            return merge_chunks_by_command(chunk_items)[0]

        else:
            # If it is a command that cannot be accurately matched, it indicates that this command is fabricated or expired. Then, use vector query for similarity search
            chunk_items = await _retrieve_chunks_from_learn_knowledge_index_service(vector_values)
            return merge_chunks_by_command(chunk_items)[0]

    # If it is a description of a subtask, use vector query for similarity search
    chunk_items = await _retrieve_chunks_from_learn_knowledge_index_service(vector_values)
    return merge_chunks_by_command(chunk_items)[0]


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


def get_top_chunks(chunks_list, top_num=3):
    sorted_chunks = sorted(chunks_list, key=lambda x: x['score'], reverse=True)
    return sorted_chunks[:top_num]
