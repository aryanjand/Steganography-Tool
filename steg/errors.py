class StegError(Exception):
    def __init__(self, message: str, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = exit_code


class FileWriteError(StegError):
    def __init__(self, message: str) -> None:
        super().__init__(message, exit_code=2)

