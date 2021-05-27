import discordy
import dotenv

import os


class MessageManager(discordy.Manager):
    async def on_MESSAGE_CREATE(self, message):
        print("Mensagem criada!")


class GuildManager(discordy.Manager):
    async def on_GUILD_CREATE(self, message):
        print("Guilda criada!")


dotenv.load_dotenv()

token = os.environ["TOKEN"]
intents = 32509
managers = (MessageManager, GuildManager,)

client = discordy.Client(token, intents, managers)
client.run()
