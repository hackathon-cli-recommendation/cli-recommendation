from enum import Enum
import os
import azure.functions as func

from common.exception import ParameterException
from common.param import get_param

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


def get_param_search_scope(req: func.HttpRequest, name: str, required=False, default=SearchScope.All):
    value = get_param(req, name, required, default)
    if isinstance(value, SearchScope):
        return value
    try:
        value = int(value)
        try:
            value = SearchScope(value)
        except ValueError:
            raise ParameterException(f'Illegal parameter: the parameter "{name}" should be 1(All), 2(Scenario) or 3(Command)')
    except ValueError:
        if isinstance(value, str):
            if value.lower() == "all":
                value = SearchScope.All
            elif value.lower() == "scenario":
                value = SearchScope.Scenario
            elif value.lower() == "command":
                value = SearchScope.Command
            else:
                raise ParameterException(f'Illegal parameter: the parameter "{name}" should be 1(All), 2(Scenario) or 3(Command)')
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
