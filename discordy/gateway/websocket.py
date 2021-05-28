import re
import aiohttp

import zlib
import json
import asyncio
from typing import Optional

from .dispatcher import Dispatcher
from .errors import ReconnectWebSocket, CloseWebSocket
from .gateway import Gateway


class WebSocket:
    DISPATCH      = 0
    HEARTBEAT     = 1
    IDENTIFY      = 2
    HELLO         = 10
    HEARTBEAT_ACK = 11

    def __init__(self, token: str, intents: int, shard_id: int,
                 gateway: Gateway, dispatcher: Dispatcher,
                 session: Optional[aiohttp.ClientSession] = None) -> None:

        self.token = token
        self.intents = intents
        self.shard_id = shard_id
        self.gateway = gateway
        self.dispatcher = dispatcher
        self.session = session

        self._exclusive_session = False

        self.socket = None
        self.loop = None
        self._closed = True
        self._buffer = bytearray()
        self._inflator = zlib.decompressobj()
        self.heartbeat_task = None

        self.session_id = None
        self.sequence = None
        self.heartbeat_interval = None

    def is_closed(self):
        return self._closed

    async def close(self):
        if self._closed:
            return

        self.heartbeat_task.cancel()
        self.heartbeat_task = None

        await self.socket.close(code=1000)
        self.socket = None

        self._closed = True

        if self._exclusive_session:
            await self.session.close()

        self.session = None
        self._exclusive_session = False

        # Reset
        self._buffer.clear()
        self.session_id = None
        self.sequence = None
        self.heartbeat_interval = None
        self.loop = None

    async def heartbeat(self):
        payload = {
            "op": self.HEARTBEAT,
            'd': self.sequence
        }

        await self.send(payload)

    async def connect(self) -> None:
        if self.session is None:
            self.session = aiohttp.ClientSession()
            self._exclusive_session = True

        self.loop = self.session.loop

        self.socket = await self.session.ws_connect(self.gateway.url)
        self._closed = False

        await self.listen()
        await self.identify()

    async def message(self, data) -> None:
        if type(data) is bytes:
            self._buffer.extend(data)

            if len(data) < 4 or not data.endswith(b"\x00\x00\xff\xff"):
                return print("returned", data)

            data = self._inflator.decompress(self._buffer)
            data = data.decode('utf-8')

            self._buffer = bytearray()

        data = json.loads(data)

        op = data["op"]

        if op is self.HEARTBEAT_ACK:
            return

        s = data.get('s')
        if s is not None:
            self.sequence = s

        d = data['d']

        if op == self.HELLO:
            self.heartbeat_interval = d["heartbeat_interval"]

            async def heartbeat():
                while not self.is_closed():
                    await self.heartbeat()
                    await asyncio.sleep(self.heartbeat_interval / 1000.0)

            task = self.loop.create_task(heartbeat())
            self.heartbeat_task = task

            return

        if op == self.DISPATCH:
            event_name = data['t']

            if event_name == "READY":
                self.session_id = d["session_id"]
                return

            if event_name == "RESUMED":
                return

            return self.dispatcher.dispatch(event_name, data)

        print(data)

    async def listen(self) -> None:
        try:
            message = await self.socket.receive(timeout=60)
        except asyncio.TimeoutError:
            raise ReconnectWebSocket

        if message.type in (aiohttp.WSMsgType.TEXT, aiohttp.WSMsgType.BINARY):
            return await self.message(message.data)

        if message.type is aiohttp.WSMsgType.ERROR:
            raise message.data

        if message.type is aiohttp.WSMsgType.CLOSE:
            raise CloseWebSocket(message.data, message.extra)

        print("leaked", message)

    def send(self, data):
        return self.socket.send_json(data)

    async def identify(self) -> None:
        import sys

        payload = {
            "op": self.IDENTIFY,
            'd': {
                "token": self.token,

                "intents": self.intents,

                "properties": {
                    "$os": sys.platform,
                    "$device": "discordy",
                    "$browser": "discordy",
                },

                "compress": bool(self.gateway.compress),

                "shard": (self.shard_id, self.gateway.shards)
            }
        }

        await self.send(payload)

    async def resume(self) -> None:
        payload = {
            "op": self.RESUME,
            'd': {
                "token": self.token,
                "session_id": self.session_id,
                "seq": self.sequence
            }
        }

        await self.send(payload)
