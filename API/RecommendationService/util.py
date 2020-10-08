import re
from enum import Enum

class RecommendType(int, Enum):
    All = 1
    Solution = 2
    Command = 3
    Scenario = 4

class CosmosType(int, Enum):
    Command = 1
    Solution = 2
    Scenario = 3

def get_cosmos_type(Recommend_type):
    if not Recommend_type:
        return

    Recommend_to_cosmos = {
        RecommendType.Command : CosmosType.Command,
        RecommendType.Solution : CosmosType.Solution,
        RecommendType.Scenario : CosmosType.Scenario
    }
    try:
        return Recommend_to_cosmos[Recommend_type]
    except KeyError:
        return None

def generated_cosmos_type(Recommend_type, has_error):
    cosmos_type = get_cosmos_type(Recommend_type)
    if cosmos_type:
        return cosmos_type
    
    if Recommend_type == RecommendType.All:
        if has_error:
            return CosmosType.Solution
        else:
            return str(CosmosType.Scenario.value) + "," + str(CosmosType.Command.value)

def need_error_info(Recommend_type):
    if Recommend_type in [ RecommendType.All, RecommendType.Solution]:
        return True
    return False

def parse_error_info(error_info):
    ''' Ignore the value and put the other parts into the array '''
    if not error_info:
        return []
    split_str = "|*Split*|"
    error_info = re.sub("\|(.*?)\|", split_str, error_info)
    return error_info.split(split_str)
