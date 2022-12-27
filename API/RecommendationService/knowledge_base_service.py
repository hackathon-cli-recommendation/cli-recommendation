from .cosmos_helper import query_recommendation_from_knowledge_base
from .util import get_latest_cmd, RecommendationSource, RecommendType


def get_recommend_from_knowledge_base(command_list, recommend_type, error_info, top_num=50):

    commands = get_latest_cmd(command_list)

    result = []
    knowledge_base_items = list(query_recommendation_from_knowledge_base(commands[-1], recommend_type, error_info))
    if knowledge_base_items:
        for item in knowledge_base_items:
            if 'nextCommand' in item:
                for command_info in item['nextCommand']:
                    command_info['source'] = RecommendationSource.KnowledgeBase
                    if error_info:
                        command_info['type'] = RecommendType.Solution
                    else:
                        command_info['type'] = RecommendType.Command
                    result.append(command_info)

            if len(result) >= top_num:
                return result[0: top_num]

    return result
