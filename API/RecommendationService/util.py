import re
from enum import Enum

class RecommandType(int, Enum):
    All = 1
    Solution = 2
    Command = 3
    Resource = 4
    Senario = 5

class CosmosType(int, Enum):
    Command = 1
    Solution = 2
    Scenario = 3

def get_cosmos_type(recommand_type):
    if not recommand_type:
        return

    recommand_to_cosmos = {
        RecommandType.Command : CosmosType.Command,
        RecommandType.Solution : CosmosType.Solution,
        RecommandType.Senario : CosmosType.Scenario
    }
    try:
        return recommand_to_cosmos[recommand_type]
    except KeyError:
        return None

def generated_cosmos_type(recommand_type, has_error):
    cosmos_type = get_cosmos_type(recommand_type)
    if cosmos_type:
        return cosmos_type
    
    if recommand_type == RecommandType.All:
        if has_error:
            return CosmosType.Solution
        else:
            return str(CosmosType.Senario) + "," + str(CosmosType.Command)

def need_error_info(recommand_type):
    if recommand_type in [ RecommandType.All, RecommandType.Solution]:
        return True
    return False

def parse_error_info(error_info):
    ''' Ignore the value and put the other parts into the array '''
    if not error_info:
        return []
    split_str = "|*Split*|"
    error_info = re.sub("\|(.*?)\|", split_str, error_info)
    return error_info.split(split_str)
