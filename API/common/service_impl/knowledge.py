from enum import Enum
import os
from typing import List, Optional

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

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
    source_filter = [ScenarioSourceType.SAMPLE_REPO, ScenarioSourceType.DOC_CRAWLER, ScenarioSourceType.MANUAL_INPUT]
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
