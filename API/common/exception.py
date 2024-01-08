from common.util import generate_response


class ParameterException(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__()
        self.msg = msg


class CopilotException(Exception):
    ERROR_CODE = 501

    def __init__(self, msg: str) -> None:
        super().__init__()
        self.msg = msg

    def to_response(self) -> str:
        return generate_response({}, self.ERROR_CODE, self.msg)


class GPTTimeOutException(CopilotException):
    ERROR_CODE = 502

    def __init__(self) -> None:
        super().__init__('GPT response Time out.')


class GPTInvalidResultException(CopilotException):
    ERROR_CODE = 503

    def __init__(self) -> None:
        super().__init__('GPT generated result could not be parsed into json')


class GPTInvalidBoolException(CopilotException):
    ERROR_CODE = 504

    def __init__(self) -> None:
        super().__init__('GPT generated result is not a bool value')


class KnowledgeSearchException(CopilotException):
    ERROR_CODE = 505

    def __init__(self) -> None:
        super().__init__('Knowledge Search Internal Error')
