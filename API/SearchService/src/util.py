from enum import Enum
import os
import azure.functions as func

from .exception import ParameterException

class SearchType(int, Enum):
    All = 1
    Scenario = 2
    Command = 3

    def get_search_fields(self):
        if self == self.All:
            return ["id", "description", "commandSet/command"]
        elif self == self.Scenario:
            return ["id", "description"]
        elif self == self.Command:
            return ["commandSet/command"]


class MatchType(int, Enum):
    All = 1
    And = 2
    Or = 3


def get_param(req: func.HttpRequest, name: str, required=True, default=None):
    value = req.params.get(name)
    if not value:
        try:
            req_body = req.get_json()
            value = req_body.get(name)
        except ValueError:
            pass
    if required and value is None:
        raise ParameterException(f'Illegal parameter: please pass in the parameter "{name}"')
    elif value is None:
        return default
    return value


def get_param_str(req: func.HttpRequest, name: str, required=False, default=""):
    value = get_param(req, name, required, default)
    if not isinstance(value, str):
        raise ParameterException(f'Illegal parameter: the parameter "{name}" must be the type of string')
    return value


def get_param_int(req: func.HttpRequest, name: str, required=False, default=0):
    try:
        return int(get_param(req, name, required, default))
    except ValueError:
        raise ParameterException(f'Illegal parameter: the parameter "{name}" must be the type of int')


def get_param_search_type(req: func.HttpRequest, name: str, required=False, default=SearchType.All):
    value = get_param(req, name, required, default)
    if isinstance(value, SearchType):
        return value
    try:
        value = int(value)
        try:
            value = SearchType(value)
        except ValueError:
            raise ParameterException(f'Illegal parameter: the parameter "{name}" should be 1(All), 2(Scenario) or 3(Command)')
    except ValueError:
        if isinstance(value, str):
            if value.lower() == "all":
                value = SearchType.All
            elif value.lower() == "scenario":
                value = SearchType.Scenario
            elif value.lower() == "command":
                value = SearchType.Command
            else:
                raise ParameterException(f'Illegal parameter: the parameter "{name}" should be 1(All), 2(Scenario) or 3(Command)')
        else:
            raise ParameterException(f'Illegal parameter: the parameter "{name}" must be the type of int or str')
    return value


def get_param_match_type(req: func.HttpRequest, name: str, required=False, default=MatchType.All):
    value = get_param(req, name, required, default)
    if isinstance(value, MatchType):
        return value
    try:
        value = int(value)
        try:
            value = MatchType(value)
        except ValueError:
            raise ParameterException(f'Illegal parameter: the parameter "{name}" should be 1(All), 2(And) or 3(Or)')
    except ValueError:
        if isinstance(value, str):
            if value.lower() == "all":
                value = MatchType.All
            elif value.lower() == "and":
                value = MatchType.And
            elif value.lower() == "or":
                value = MatchType.Or
            else:
                raise ParameterException(f'Illegal parameter: the parameter "{name}" should be 1(All), 2(And) or 3(Or)')
        else:
            raise ParameterException(f'Illegal parameter: the parameter "{name}" must be the type of int or str')
    return value


def build_search_statement(keyword: str, match_type: MatchType) -> str:
    if match_type == MatchType.Or:
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
            word = word + "~"
        search_statement.append(word)
    return join_word.join(search_statement)

def append_results(results, appended_results):
    for result in appended_results:
        if not next(filter(lambda item: item["scenario"] == result["scenario"], results), None):
            results.append(result)
