import os
from typing import Any, Dict, List
import json
import openai
from openai.error import TryAgain, Timeout, OpenAIError, RateLimitError
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
def gpt_generate(system_msg: str, user_msg: str, history_msg: List[Dict[str, str]]) -> str:
    # the param dict of the chatgpt service
    chatgpt_service_params = initialize_chatgpt_service_params(system_msg)
    all_user_msg = []
    if history_msg:
        chatgpt_service_params["messages"].extend(history_msg)
        all_user_msg = [msg["content"]
                        for msg in history_msg if msg["role"] == "user"]
    all_user_msg.append(user_msg)
    chatgpt_service_params["messages"].append(
        {"role": "user", "content": "\n".join(all_user_msg)})
    try:
        response = openai.ChatCompletion.create(**chatgpt_service_params)
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
