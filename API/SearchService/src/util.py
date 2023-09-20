from enum import Enum
import json
import os
import azure.functions as func

from common.exception import ParameterException
from common.util import get_param

class SearchScope(int, Enum):
    All = 1
    Scenario = 2
    Command = 3
    Keyword = 4

    def get_search_fields(self):
        if self == self.All:
            return ["name", "description", "commandSet/command"]
        elif self == self.Scenario:
            return ["name", "description"]
        elif self == self.Command:
            return ["commandSet/command"]
        elif self == self.Keyword:
            return ["keyword"]


class MatchRule(int, Enum):
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


def get_param_list(req: func.HttpRequest, name: str, required=False, default=[]):
    value = get_param(req, name, required, default)
    try:
        return list(value)
    except ValueError:
        raise ParameterException(
            f'Illegal parameter: the parameter "{name}" must be the type of list')


def is_valid_json(json_str):
    try:
        json.loads(json_str)
        return True
    except json.JSONDecodeError:
        return False


def get_param_search_scope(req: func.HttpRequest, name: str, required=False, default=SearchScope.All):
    value = get_param(req, name, required, default)
    if isinstance(value, SearchScope):
        return value
    try:
        value = int(value)
        try:
            value = SearchScope(value)
        except ValueError:
            raise ParameterException(f'Illegal parameter: the parameter "{name}" should be 1(All), 2(Scenario) or 3(Command) or 4(keyword)')
    except ValueError:
        if isinstance(value, str):
            if value.lower() == "all":
                value = SearchScope.All
            elif value.lower() == "scenario":
                value = SearchScope.Scenario
            elif value.lower() == "command":
                value = SearchScope.Command
            elif value.lower() == "keyword":
                value = SearchScope.Keyword
            else:   
                raise ParameterException(f'Illegal parameter: the parameter "{name}" should be 1(All), 2(Scenario) or 3(Command) or 4(keyword)')
        else:
            raise ParameterException(f'Illegal parameter: the parameter "{name}" must be the type of int or str')
    return value


def get_param_match_rule(req: func.HttpRequest, name: str, required=False, default=MatchRule.All):
    value = get_param(req, name, required, default)
    if isinstance(value, MatchRule):
        return value
    try:
        value = int(value)
        try:
            value = MatchRule(value)
        except ValueError:
            raise ParameterException(f'Illegal parameter: the parameter "{name}" should be 1(All), 2(And) or 3(Or)')
    except ValueError:
        if isinstance(value, str):
            if value.lower() == "all":
                value = MatchRule.All
            elif value.lower() == "and":
                value = MatchRule.And
            elif value.lower() == "or":
                value = MatchRule.Or
            else:
                raise ParameterException(f'Illegal parameter: the parameter "{name}" should be 1(All), 2(And) or 3(Or)')
        else:
            raise ParameterException(f'Illegal parameter: the parameter "{name}" must be the type of int or str')
    return value


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
