import json
import logging
import os
from enum import Enum
from typing import List, Optional

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from common.exception import GPTInvalidBoolException
from common.service_impl.chatgpt import gpt_generate, num_tokens_from_message
from common.util import ScenarioSourceType


class SearchScope(int, Enum):
    All = 1
    Scenario = 2
    Command = 3

    def get_search_fields(self):
        if self == self.All:
            return ["name", "description", "commandSet/command"]
        elif self == self.Scenario:
            return ["name", "description"]
        elif self == self.Command:
            return ["commandSet/command"]


class MatchRule(int, Enum):
    All = 1
    And = 2
    Or = 3


class SearchType(int, Enum):
    Semantic = 1
    FullText = 2
    Keyword = 3

def knowledge_search(keyword: str, top_num: int):
    # placeholder for rate limit
    exceed_rate_limit = False
    if not exceed_rate_limit:
        results = knowledge_search_semantic(keyword, top_num)
    else:
        results = knowledge_search_full_text(keyword, top_num)
    return results


def knowledge_search_semantic(keyword: str, top_num: int, scope=SearchScope.Scenario):
    # source_filter = [ScenarioSourceType.SAMPLE_REPO, ScenarioSourceType.DOC_CRAWLER, ScenarioSourceType.MANUAL_INPUT]
    # To ensure quality, only search scenarios which source equal to 1
    source_filter = [ScenarioSourceType.SAMPLE_REPO]
    results = get_search_results(keyword, source_filter, top_num, scope.get_search_fields(), SearchType.Semantic)
    return results


def knowledge_search_full_text(keyword: str, top_num: int, scope=SearchScope.Scenario, match_rule=MatchRule.All):
    if os.environ["ENABLE_CLAWLER_SCENARIOS"].lower() == "true":
        source_filter = [ScenarioSourceType.SAMPLE_REPO, ScenarioSourceType.DOC_CRAWLER]
    else:
        source_filter = [ScenarioSourceType.SAMPLE_REPO]
    results = get_search_results(build_search_statement(keyword, match_rule), source_filter, top_num, scope.get_search_fields(), SearchType.FullText)
    if len(keyword.split()) > 1 and len(results) < top_num and match_rule == MatchRule.All:
        or_results = get_search_results(build_or_search_statement(keyword), source_filter, top_num, scope.get_search_fields(), SearchType.FullText)
        append_results(results, or_results)
        results = results[:top_num]
    return results


def get_search_results(
        search_statement: str, source_filter: List[ScenarioSourceType],
        top: int = 5, search_fields: Optional[List[str]] = None, search_type=SearchType.Semantic):
    service_endpoint = os.environ["SCENARIO_SEARCH_SERVICE_ENDPOINT"]
    search_client = SearchClient(endpoint=service_endpoint,
                                 index_name=os.environ["SCENARIO_SEARCH_INDEX"],
                                 credential=AzureKeyCredential(os.environ["SCENARIO_SEARCH_SERVICE_SEARCH_KEY"]))

    filter = " or ".join([f"(source eq {src})" for src in source_filter])
    if search_type == SearchType.Semantic:

        results = search_client.search(
            query_answer='extractive',
            query_caption='extractive',
            query_language='en-us',
            semantic_configuration_name='semanctic-config',
            search_text=search_statement,
            filter=filter,
            include_total_count=True,
            search_fields=search_fields,
            query_caption_highlight=True,
            highlight_fields=", ".join(search_fields) if search_fields else None,
            top=top,
            query_type='semantic')
    elif search_type == SearchType.FullText:
        results = search_client.search(
            search_text=search_statement,
            filter=filter,
            include_total_count=True,
            search_fields=search_fields,
            highlight_fields=", ".join(search_fields) if search_fields else None,
            top=top,
            query_type='full')
    results = list(results)
    for result in results:
        result.pop("rid")
        if search_type == SearchType.Semantic:
            result["score"] = result.pop("@search.reranker_score")
            captions = result.pop("@search.captions")
            captions_highlights = []
            for caption in captions:
                captions_highlights.append(caption.highlights)
                result["highlights"] = {"scenario": ';'.join(captions_highlights)}
        elif search_type == SearchType.FullText:
            result["score"] = result.pop("@search.score")
            result["highlights"] = result.pop("@search.highlights")
            if result["highlights"] and "name" in result["highlights"].keys():
                result["highlights"]["scenario"] = result["highlights"].pop("name")
        result["scenario"] = result.pop("name")
    return results


def build_search_statement(keyword: str, match_rule: MatchRule) -> str:
    if match_rule == MatchRule.Or:
        return build_or_search_statement(keyword)
    else:
        return build_and_search_statement(keyword)


def build_and_search_statement(keyword: str) -> str:
    return _build_search_statement(keyword, join_word=" AND ")


def build_or_search_statement(keyword: str) -> str:
    return _build_search_statement(keyword, join_word=" OR ")


def _build_search_statement(keyword: str, join_word=" AND ") -> str:
    search_statement = []
    exact_length = os.environ.get("EXACT_MATCH_LENGTH", 3)
    dist1_length = os.environ.get("DISTANCE_1_MATCH_LENGTH", 5)
    for word in keyword.split():
        if not word:
            continue
        if len(word) <= exact_length:
            word = word
        elif len(word) <= dist1_length:
            word = word + "~1"
        else:
            word = word + "~2"
        search_statement.append(word)
    return join_word.join(search_statement)

def append_results(results, appended_results):
    for result in appended_results:
        if not next(filter(lambda item: item["scenario"] == result["scenario"], results), None):
            results.append(result)


def pass_verification(context, question, result):
    if result[0]['score'] < float(os.environ.get('KNOWLEDGE_QUALITY_THRESHOLD', "1.0")):
        return False
    else:
        answer = result[0]['description']
        user_msg = f"question: {question}\ndescription: {answer}"
        default_msg = r"""[{"role":"system","content":"Give you a question and a description, please refer to the following rules to determine if the content in the question is completely consistent with the description:\n1. Please determine whether the content in the question is semantically consistent with the description. If inconsistent, output False directly and do not need to continue with subsequent steps.\n2. Analyze the resources and operations on resources included in the question and description separately, and clarify what operations are used on what resources.\n3. Confirm whether the resources, operations, and corresponding relationships between operations and resources included in the question are completely consistent with the description. If they are the same or very close, output True, otherwise output False."},{"role":"user","content":"question: How to create a VM snapshot from VM image.\ndescription: Tutorial to create a VM image from an existing VM."},{"role":"assistant","content":"False"},{"role":"user","content":"question: I want to create a VM snapshot from VM image, could you give some suggestion?\ndescription: Tutorial to create a VM snapshot from an existing VM image."},{"role":"assistant","content":"True"}]"""
        check_similarity_msg = os.environ.get("OPENAI_CHECK_KNOWLEDGE_SEARCH_SIMILARITY_MSG", default=default_msg)
        context.custom_context.gpt_task_name = 'CHECK_KNOWLEDGE_SEARCH_SIMILARITY'
        context.custom_context.estimated_question_tokens = num_tokens_from_message(user_msg)
        content = gpt_generate(context, check_similarity_msg, user_msg, history_msg=[])
        content = content.replace("\"", "").replace("'", "").lower()
        if content not in ['true', 'false']:
            logging.error(f"Not a bool value error: {content}")
            raise GPTInvalidBoolException
        return True if content == 'true' else False
