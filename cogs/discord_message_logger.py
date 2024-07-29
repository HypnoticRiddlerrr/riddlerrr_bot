import aiohttp
from config import Config
from keyrings.cryptfile.cryptfile import CryptFileKeyring
from twitchio import Message
from twitchio.ext import commands

keyring = CryptFileKeyring()
config = Config("./config.cfg")

with open("./secrets/keyring_password", mode="r", encoding="UTF-8") as file:
    keyring.keyring_key = file.read().strip()


class DiscordMessageLogger(commands.Cog):
    def __init__(self, bot: commands.Bot, webhook_url: str):
        self.bot = bot
        self.webhook_url = webhook_url

    @commands.Cog.event()
    async def event_message(self, message: Message) -> None:
        """
        Handles actions upon receiving a message in the Twitch chat.

        This asynchronous method processes incoming messages and performs specific actions
        based on the message content and tags. If the message contains a custom reward ID,
        it triggers the corresponding action such getting a riddle.

        Args:
            message (Message): The message object received from the Twitch chat. This
            includes information about the message content, sender, and any associated tags.

        Returns:
            None

        Raises:
            None: This method does not raise any exceptions.

        Actions:
            - If the message is an echo, it is ignored.
            - If the message contains the custom reward ID for getting a riddle, it calls the
            `get_a_riddle` method.

        Example:
            When a user redeems a custom reward with the ID "3021857f-d329-4de0-85ff-b557375849f5",
            the bot will fetch and display a riddle.
        """
        if message.echo:
            await self.log_bot_message_to_discord(message_content=message.content)
            return
        await self.log_user_message_to_discord(
            commands.Context(
                prefix=None,
                content=message.content,
                message=message,
                bot=self,
            )
        )

    async def log_bot_message_to_discord(self, message_content: str) -> None:
        async with aiohttp.ClientSession() as session:
            await session.post(
                url=self.webhook_url,
                data={
                    "username": "RiddlerrrBOT",
                    "content": message_content,
                },
            )

    async def log_user_message_to_discord(self, ctx: commands.Context) -> None:
        async with aiohttp.ClientSession() as session:
            await session.post(
                url=self.webhook_url,
                data={
                    "username": ctx.author.display_name,
                    "content": ctx.message.content,
                },
            )


def prepare(bot: commands.Bot) -> None:
    """
    Prepare the bot by adding the MyCog cog.

    This function is called to register the MyCog cog with the provided bot instance.
    It initializes the MyCog class and uses the bot's `add_cog` method to add it to the bot.

    Args:
        bot (commands.Bot): The instance of the bot to which the cog should be added.
    """
    bot.add_cog(
        DiscordMessageLogger(
            bot,
            config["CHAT_TO_DISCORD_WEBHOOK_URL"],
        )
    )
