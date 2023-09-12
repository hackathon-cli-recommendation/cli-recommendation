import json
import logging
import os

import azure.functions as func

from common.exception import ParameterException
from common.util import ScenarioSourceType, get_param_int, get_param_str, get_param_list
from .src.search_service import get_search_results

from .src.util import MatchRule, SearchScope, append_results, build_or_search_statement, build_search_statement, get_param_match_rule, get_param_search_scope
from ..ChatgptService import ask_chatgpt_service

# nl2keyword process switch
nl2keyword = os.environ["ENABLE_NL2KEYWORD"]

def main(req: func.HttpRequest,
         context: func.Context) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        keyword = get_param_str(req, "keyword", required=True)
        if nl2keyword.lower() == "true":
            question = user_msg = keyword
            history_msg = get_param_list(req, "history_msg")
            openai_prompt = json.loads(os.environ.get('OPENAI_NL2KEYWORD_MSG'))
            res = json.loads(ask_chatgpt_service(user_msg, history_msg, openai_prompt))
            if res["status"] != 200:
                logging.error('There is some error from the openai server.')
            else:
                logging.info('Successfully get the response from the openai server.')
                keyword = ' '.join(res['data']['content']) if res['data']['content'] else keyword
                logging.info('The opneai service converts the question %s into keywords %s', question, keyword)
        search_scope = get_param_search_scope(req, "scope", default=SearchScope.All)
        top_num = get_param_int(req, "top_num", default=5)
        if top_num <=0 or top_num > 20:
            raise ParameterException("Illegal parameter: the parameter 'top_num' must be in the range 1-20")
        match_rule = get_param_match_rule(req, "match_rule", default=MatchRule.All)
    except ParameterException as e:
        return func.HttpResponse(e.msg, status_code=400)

    # escape special characters
    # keyword = escape_special_characters(keyword)

    if os.environ["ENABLE_CLAWLER_SCENARIOS"].lower() == "true":
        source_filter = [ScenarioSourceType.SAMPLE_REPO, ScenarioSourceType.DOC_CRAWLER]
    else:
        source_filter = [ScenarioSourceType.SAMPLE_REPO]
    results = get_search_results(build_search_statement(keyword, match_rule), source_filter, top_num, search_scope.get_search_fields())
    if len(keyword.split()) > 1 and len(results) < top_num and match_rule == MatchRule.All:
        or_results = get_search_results(build_or_search_statement(keyword), source_filter, top_num, search_scope.get_search_fields())
        append_results(results, or_results)
        results = results[:top_num]
    return func.HttpResponse(json.dumps({
        'data': results,
        'error': None,
        'status': 200,
        # The version of the API, which is defined in the function app settings and can be changed without redeploying the whole function.
        'api_version': os.environ["API_Version"]
    }), status_code=200)

def escape_special_characters(input_string):
    # TODO: modify the special_characters list according to the search service or let user escape the special characters by themselves.
    # https://learn.microsoft.com/en-us/azure/search/query-lucene-syntax#escaping-special-characters
    # The backslash character \ in the list of special_characters also needs to be represented with a double backslash \\ in order to correctly represent the backslash character itself.
    # special_characters = ['+', '-', '&', '|', '!', '(', ')', '{', '}', '[', ']', '^', '"', '~', '*', '?', ':', '\\', '/']
    # according to case Restart/Stop/Start an Azure Database for MySQL - Flexible Server. / and - are not special characters.
    special_characters = ['+', '&', '|', '!', '(', ')', '{', '}', '[', ']', '^', '"', '~', '*', '?', ':', '\\']
    # according to case Azure CLI scripts for throughput (RU/s) operations for Azure Cosmos DB Gremlin API resources, / is a special character.
    # Exception: HttpResponseError: (InvalidRequestParameter) Failed to parse query string at line 1, column 165. See https://aka.ms/azure-search-full-query for supported syntax.
    escaped_string = ""

    for char in input_string:
        if char in special_characters:
            escaped_string += '\\' + char
        else:
            escaped_string += char

    return escaped_string
