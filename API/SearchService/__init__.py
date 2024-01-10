import json
import logging
import os

import azure.functions as func

from common.exception import ParameterException
from common.util import ScenarioSourceType
from common.param import get_param_int, get_param_str
from .src.search_service import get_search_results

from .src.util import MatchRule, SearchScope, append_results, build_or_search_statement, build_search_statement, get_param_match_rule, get_param_search_scope


def main(req: func.HttpRequest,
         context: func.Context) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        keyword = get_param_str(req, "keyword", required=True)
        search_scope = get_param_search_scope(req, "scope", default=SearchScope.All)
        top_num = get_param_int(req, "top_num", default=5)
        if top_num <=0 or top_num > 20:
            raise ParameterException("Illegal parameter: the parameter 'top_num' must be in the range 1-20")
        match_rule = get_param_match_rule(req, "match_rule", default=MatchRule.All)
    except ParameterException as e:
        return func.HttpResponse(e.msg, status_code=400)

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
