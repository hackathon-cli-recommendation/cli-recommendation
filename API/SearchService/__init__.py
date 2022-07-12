import json
import logging

import azure.functions as func
from .src.exception import ParameterException
from .src.search_service import get_search_results

from .src.util import SearchType, get_param_int, get_param_search_type, get_param_str


def main(req: func.HttpRequest,
         context: func.Context) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        keyword = get_param_str(req, "keyword")
        search_type = get_param_search_type(req, "type", SearchType.All)
        top_num = get_param_int(req, "top_num", 5)
    except ParameterException as e:
        return func.HttpResponse(e.msg, status_code=400)
    results = get_search_results(
        keyword, top_num, search_type.get_search_fields())
    return func.HttpResponse(json.dumps({
        'data': results,
        'error': None,
        'status': 200
    }), status_code=200)
