from common.util import generate_response


class CopilotException(Exception):
    ERROR_CODE = 501

    def __init__(self, msg: str) -> None:
        super().__init__()
        self.msg = msg

    def to_response_body(self) -> str:
        return generate_response(None, self.ERROR_CODE, self.msg)


class UserException(CopilotException):
    ERROR_CODE = 400

    def __init__(self, msg: str):
        super().__init__(msg)


class ParameterException(UserException):
    ERROR_CODE = 401

    def __init__(self, msg: str) -> None:
        super().__init__(msg)


class QuestionOutOfScopeException(UserException):
    ERROR_CODE = 402

    def __init__(self, msg: str) -> None:
        super().__init__(msg)


class ServiceException(CopilotException):
    ERROR_CODE = 502

    def __init__(self, msg: str):
        super().__init__(msg)


class GPTException(ServiceException):
    ERROR_CODE = 503

    def __init__(self, msg: str):
        super().__init__(msg)


class GPTTimeOutException(GPTException):
    ERROR_CODE = 504

    def __init__(self) -> None:
        super().__init__('GPT response Time out.')


class GPTInvalidResultException(GPTException):
    ERROR_CODE = 505

    def __init__(self) -> None:
        super().__init__('GPT generated result could not be parsed into json')


class GPTInvalidBoolException(GPTException):
    ERROR_CODE = 506

    def __init__(self) -> None:
        super().__init__('GPT generated result is not a bool value')


class KnowledgeSearchException(ServiceException):
    ERROR_CODE = 507

    def __init__(self) -> None:
        super().__init__('Knowledge Search Internal Error')
