import os
from typing import Any, Dict, List
import json
import openai
from openai.error import TryAgain, Timeout, OpenAIError, RateLimitError
import tiktoken
import logging

from common.exception import CopilotException, GPTTimeOutException
from common.util import timing_decorator


logger = logging.getLogger(__name__)


# initialize_openai_service
# the type of the OpenAI API service
openai.api_type = "azure"
# the key of the OpenAI API service
openai.api_key = os.environ["OPENAI_API_KEY"]
# the version of the OpenAI API service
openai.api_version = os.environ["OPENAI_API_VERSION"]
# the url of the OpenAI API service
openai.api_base = os.environ["OPENAI_API_URL"]


@timing_decorator
def gpt_generate(system_msg: str, user_msg: str, history_msg: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
    # the param dict of the chatgpt service
    chatgpt_service_params = initialize_chatgpt_service_params(system_msg)
    all_user_msg = []
    if history_msg:
        history_tokens = num_tokens_from_messages(history_msg)
        chatgpt_service_params["messages"].extend(history_msg)
        all_user_msg = [msg["content"]
                        for msg in history_msg if msg["role"] == "user"]
    all_user_msg.append(user_msg)
    chatgpt_service_params["messages"].append(
        {"role": "user", "content": "\n".join(all_user_msg)})
    prompt_tokens = num_tokens_from_messages(chatgpt_service_params["messages"])
    gpt_task_name = kwargs.get('gpt_task_name', 'undefined')
    message = f"The estimated cost of {gpt_task_name} GPT call is as follows: "
    message += f"question tokens = {kwargs['question_tokens']}, " if 'question_tokens' in kwargs else ""
    message += f"task list tokens = {kwargs['task_list_tokens']}, task lens = {kwargs['task_list_lens']}, " if 'task_list_tokens' in kwargs else ""
    message += f"usage tokens = {kwargs['usage_tokens']}, " if 'usage_tokens' in kwargs else ""
    message += f"history tokens = {history_tokens}, " if 'history_tokens' in kwargs else ""
    message += f"propmpt tokens = {prompt_tokens}."
    logging.info(f"{message}")
    try:
        response = openai.ChatCompletion.create(**chatgpt_service_params)
        logging.info(f"The actual cost of {gpt_task_name} GPT call is as follows: completion tokens = {response['usage']['completion_tokens']}, propmpt tokens = {response['usage']['prompt_tokens']}, total tokens = {response['usage']['total_tokens']}.")
    except (TryAgain, Timeout) as e:
        raise GPTTimeOutException() from e
    except RateLimitError as e:
        raise CopilotException('The OpenAI API rate limit is exceeded.') from e
    except OpenAIError as e:
        raise CopilotException('There is some error from the OpenAI.') from e
    content = response["choices"][0]["message"]["content"]

    return content


def initialize_chatgpt_service_params(prompt_msg=None, chatgpt_service_params=None):
    # use a dict to store the parameters of the chatgpt service
    # give initial values to the parameters

    if not chatgpt_service_params:
        chatgpt_service_params = {"engine": "GPT_4_32k", "temperature": 0.5, "max_tokens": 4000, 
                                  "top_p": 0.95, "frequency_penalty": 0, "presence_penalty": 0, "stop": None}

    for key, value in chatgpt_service_params.items():
        chatgpt_service_params[key] = os.environ.get(key, default=value)
        if key in ["temperature", "top_p"]:
            chatgpt_service_params[key] = float(chatgpt_service_params[key])
        elif key in ["max_tokens", "frequency_penalty", "presence_penalty"]:
            chatgpt_service_params[key] = int(chatgpt_service_params[key])
    chatgpt_service_params["messages"] = json.loads(prompt_msg)
    return chatgpt_service_params


def num_tokens_from_messages(messages: List[Dict[str, str]], model="gpt-3.5-turbo-0613"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo-0613":  # note: future models may deviate from this
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += -1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens
    else:
        logging.error(f"""num_tokens_from_messages() is not presently implemented for model {model}.
    See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")
        return None

def num_tokens_from_message(message: str, model="gpt-3.5-turbo-0613"):
    """Returns the number of tokens used by a messages."""
    if not isinstance(message, str):
        message = str(message)
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo-0613":  # note: future models may deviate from this
        num_tokens = len(encoding.encode(message))
        return num_tokens
    else:
        logging.error(f"""num_tokens_from_message() is not presently implemented for model {model}.
    See https://github.com/openai/openai-python/blob/main/chatml.md for information on how message is converted to tokens.""")
        return None
