import asyncio

import signal

import aiohttp

from .core import GatewayWebSocket
from . import event


class Client:
    def __init__(self, token, intents, managers, *, loop = None):
        self.token = token
        self.intents = intents

        managers = (m(self) for m in managers)
        self.handler = event.Handler(managers)

        self.loop = loop or asyncio.get_event_loop()

        self.ws = None
        self.session = None
        self._closed = False

    def is_closed(self):
        return self._closed

    async def close(self):
        if self._closed:
            return

        self._closed = True

    async def login(self):
        self.session = aiohttp.ClientSession()

    async def connect(self):
        self.ws = GatewayWebSocket(self.token, self.intents)
        await self.ws.connect(self.session, self.handler)

        while not self.is_closed():
            await self.ws.poll_event()

    async def start(self):
        try:
            await self.login()
            await self.connect()
        finally:
            await self.close()

    def run(self):
        loop = self.loop

        future = self.start()
        future = asyncio.ensure_future(future, loop=loop)

        def callback(_):
            loop.stop()

        future.add_done_callback(callback)

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            future.remove_done_callback(callback)

            gens = loop.shutdown_asyncgens()
            loop.run_until_complete(gens)

        if not future.cancelled():
            return future.result()
