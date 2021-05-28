import typing


import asyncio
from typing import Callable, Optional


class Dispatcher:
    def wait_for(self, name: str, check: Callable[[dict], bool],
                 timeout: Optional[int] = None):

        return NotImplemented

        future = asyncio.Future()

        return asyncio.wait_for(future, timeout=timeout)

    def dispatch(self, name: str, data: dict) -> None:
        print(name)
