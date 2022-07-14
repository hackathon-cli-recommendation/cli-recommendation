from typing import List, Optional
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

import os


def get_search_results(keyword: str, top: int = 5, search_fields: Optional[List[str]] = None):
    service_endpoint = os.environ["SCENARIO_SEARCH_SERVICE_ENDPOINT"]
    search_client = SearchClient(endpoint=service_endpoint,
                                 index_name=os.environ["SCENARIO_SEARCH_INDEX"],
                                 credential=AzureKeyCredential(os.environ["SCENARIO_SEARCH_SERVICE_SEARCH_KEY"]))

    query_type = 'full'
    results = search_client.search(
        search_text=keyword, include_total_count=True, search_fields=search_fields, highlight_fields=", ".join(search_fields), top=top, query_type=query_type)
    results = list(results)
    for result in results:
        result.pop("rid")
        result["score"] = result.pop("@search.score")
        result["highlights"] = result.pop("@search.highlights")
        result["scenario"] = result.pop("id")
        if "id" in result["highlights"].keys():
            result["highlights"]["scenario"] = result["highlights"].pop("id")
    return results
