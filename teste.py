import aiohttp
import asyncio

import itertools

from discordy import GatewayWebSocket


GATEWAY = "wss://gateway.discord.gg/?v=9&encoding=json"

INTENTS = 32509
TOKEN = "token aq"


async def main():
    async with aiohttp.ClientSession() as session:
        ws = GatewayWebSocket(TOKEN, INTENTS)
        await ws.connect(session)

        for _ in itertools.count():
            await ws.poll_event()


asyncio.run(main())
