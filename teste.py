from dotenv import load_dotenv
import discordy

import os
import asyncio

load_dotenv()


async def main():
    token = os.environ["TOKEN"]

    d = discordy.Dispatcher()
    g = discordy.Gateway(url="wss://gateway.discord.gg", version=9)
    ws = discordy.WebSocket(token, 32509, 0, g, d)

    await ws.connect()

    while not ws.is_closed():
        await ws.listen()

    await ws.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
