import os
import requests
import json
import logging
import re

from common.util import determine_strings_are_similar, parse_command_info

# learn knowledge index service endpoint URL  
learn_knowledge_index_url = os.environ["LEARN_KNOWLEDGE_INDEX_SERVICE_URL"]

embedding_model_url = os.environ["EMBEDDING_MODEL_URL"]


def _embedding_text_to_vector(text):

    headers = {
        'Content-Type': 'application/json',
        'api-key': os.environ["OPENAI_API_KEY"]
    }

    payload = {
        "input": text
    }

    result = requests.post(embedding_model_url, json.dumps(payload), headers=headers)
    if result.status_code != 200:
        logging.error('Status:{} {} ErrorMessage:{}'.format(result.status_code, result.reason, result.text))
        return []
    if not result.data or not result.data[0].embedding:
        logging.error('No embedding vector for the text {}', text)
        return []

    return result.data[0].embedding


def _retrieve_chunks_from_learn_knowledge_index_service(vector_values, filter_command=None):  # pylint: disable=unused-argument

    headers = {
        'Content-Type': 'application/json',
        'Authorization': os.environ["LEARN_KNOWLEDGE_INDEX_ACCESS_TOKEN"]
    }

    filter = "depotName eq 'Azure.azure-cli-docs'"
    if filter_command:
        filter = "({}) and (title eq '{}')".format(filter, filter_command)

    payload = {
        "filter": filter,
        "vector":{
            "values": vector_values,
            "top": os.environ["RETRIEVED_NUMBER_OF_CHUNKS"]
        }
    }

    score_threshold = os.environ["LEARN_KNOWLEDGE_INDEX_SCORE_THRESHOLD"]
    if score_threshold:
        learn_knowledge_index_url = learn_knowledge_index_url + "?scoreThreshold=" + score_threshold

    result = requests.post(learn_knowledge_index_url, json.dumps(payload), headers=headers)
    if result.status_code != 200:
        logging.error('Status:{} {} ErrorMessage:{}'.format(result.status_code, result.reason, result.text))
        return []
    if not result.items:
        logging.error('No retrieved chunks')
        return []

    return convert_chunks_to_json(result.items)


def retrieve_chunks_for_atomic_task(task_info):
    vector_values = _embedding_text_to_vector(task_info)

    is_command = task_info.startswith("az ")
    if is_command:
        command_info, parameters_info = parse_command_info(task_info)
        chunk_items = _retrieve_chunks_from_learn_knowledge_index_service(vector_values, filter_command=command_info)
        # If the split subtask is a correct command, then accurately search for chunks related to this command
        if chunk_items:
            command_chunks_info = merge_chunks_by_command(chunk_items)[0]

        else:
            # If it is a command that cannot be accurately matched, it indicates that this command is fabricated or expired. Then, use vector query for similarity search
            chunk_items = _retrieve_chunks_from_learn_knowledge_index_service(vector_values)



    # If it is a description of a subtask, use vector query for similarity search
    return _retrieve_chunks_from_learn_knowledge_index_service(vector_values)


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
