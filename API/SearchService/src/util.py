from enum import Enum
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
