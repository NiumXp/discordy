import asyncio
import aiohttp

import json
import sys

GATEWAY = "wss://gateway.discord.gg/?v=9&encoding=json"


class Op:
    DISPATCH           = 0
    HEARTBEAT          = 1
    IDENTIFY           = 2
    RESUME             = 6
    HELLO              = 10
    HEARTBEAT_ACK      = 11


class GatewayWebSocket:
    MAX_HEARTBEAT_TIMEOUT = 60

    def __init__(self, token, intents) -> None:
        self.token = token
        self.intents = intents

        self.loop = None
        self.socket = None
        self.sequence = None
        self.session_id = None
        self.heartbeat_interval = None

    def send(self, data, *, to_json=True):
        if to_json is True:
            data = json.dumps(data, separators=(',', ':'), ensure_ascii=True)
        return self.socket.send_str(data)

    async def connect(self, session: aiohttp.ClientSession):
        self.loop = session.loop
        self.socket = await session.ws_connect(GATEWAY)

        await self.poll_event()
        await self.identify()

    async def dispatch(self, event, data):
        if event not in ["GUILD_CREATE", "MESSAGE_CREATE"]:
            print(event, data)
        else:
            print(event)

    async def heartbeat(self):
        payload = {"op": Op.HEARTBEAT}
        while True:
            payload['d'] = self.sequence
            await self.send(payload)

            await asyncio.sleep(self.heartbeat_interval / 1000.0)

    async def received_message(self, message):
        message = json.loads(message)

        opcode = message.get("op")
        data = message.get('d')

        seq = message.get('s')
        if seq is not None:
            self.sequence = seq

        if opcode != Op.DISPATCH:
            if opcode == Op.HELLO:
                self.heartbeat_interval = data["heartbeat_interval"]
                return print("HELLO", message)

            if opcode == Op.HEARTBEAT_ACK:
                print("HEARTBEAT_ACK", message)
                return

            if opcode == Op.HEARTBEAT:
                print("HEARTBEAT")
                return

            print("leaked", message)
            return

        event = message.get('t')

        if event == "READY":
            self.sequence = message['s']
            self.session_id = data['session_id']

            self.loop.create_task(self.heartbeat())
            return

        if event == "RESUME":
            return print("RESUME")

        await self.dispatch(event, data)

    async def poll_event(self):
        message = await self.socket.receive(self.MAX_HEARTBEAT_TIMEOUT)

        if message.type is aiohttp.WSMsgType.TEXT:
            return await self.received_message(message.data)

        if message.type is aiohttp.WSMsgType.ERROR:
            raise message.data

        if message.type is aiohttp.WSMsgType.CLOSE:
            print(message)
            raise Exception("fechar conexão")

        if message.type is aiohttp.WSMsgType.CLOSED:
            print(message)
            raise Exception("Conexão fechada")

        print(message)

    async def identify(self):
        payload = {
            "op": Op.IDENTIFY,
            "d": {
                "token": self.token,
                "intents": self.intents,
                "properties": {
                    "$os": sys.platform,
                    "$browser": "discordy",
                    "$device": "discordy",
                }
            }
        }

        await self.send(payload)
