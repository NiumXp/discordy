class ReconnectWebSocket(Exception):
    pass


class CloseWebSocket(Exception):
    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
 
        super().__init__(f"[{code}] {message}")
