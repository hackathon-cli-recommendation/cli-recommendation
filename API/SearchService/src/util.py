from enum import Enum
import azure.functions as func

from .exception import ParameterException

class SearchType(int, Enum):
    All = 1
    Scenario = 2
    Command = 3

    def get_search_fields(self):
        if self == self.All:
            return ["scenario", "description", "commandSet/command"]
        elif self == self.Scenario:
            return ["scenario", "description"]
        elif self == self.Command:
            return ["commandSet/command"]


class RequiredParameter:
    pass


def get_param(req: func.HttpRequest, name: str, default=RequiredParameter):
    value = req.params.get(name)
    if not value:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            value = req_body.get(name, default)
    if value == RequiredParameter:
        raise ParameterException(f'Illegal parameter: please pass in the parameter "{name}"')
    return value


def get_param_str(req: func.HttpRequest, name: str, default=RequiredParameter):
    value = get_param(req, name, default)
    if not isinstance(value, str):
        raise ParameterException(f'Illegal parameter: the parameter "{name}" must be the type of string')
    return value
        

def get_param_int(req: func.HttpRequest, name: str, default=RequiredParameter):
    try:
        return int(get_param(req, name, default))
    except ValueError:
        raise ParameterException(f'Illegal parameter: the parameter "{name}" must be the type of int')


def get_param_search_type(req: func.HttpRequest, name: str, default=RequiredParameter):
    value = get_param(req, name, default)
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
