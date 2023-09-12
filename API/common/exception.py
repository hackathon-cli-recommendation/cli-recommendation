class ParameterException(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__()
        self.msg = msg


class CopilotException(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__()
        self.msg = msg


class GPTTimeOutException(CopilotException):
    def __init__(self) -> None:
        super().__init__('GPT response Time out.')


class GPTInvalidResultException(CopilotException):
    def __init__(self, result) -> None:
        super().__init__('Generate Result Could be Parsed into json: {}'.format(result))
