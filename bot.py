"""Script to run a Twitch BOT with custom features (watch time, fun commands, spotify integration etc)"""

import json

import aiohttp
import motor
import motor.motor_asyncio
import requests
from config import Config
from keyrings.cryptfile.cryptfile import CryptFileKeyring
from twitchio.ext import commands, pubsub

from utils import ChannelInfo

keyring = CryptFileKeyring()
config = Config("./config.cfg")

with open("./secrets/keyring_password", mode="r", encoding="UTF-8") as file:
    keyring.keyring_key = file.read().strip()


class Bot(commands.Bot):
    """
    Represents a Twitch chat bot with additional functionalities.

    This class encapsulates the functionalities of a Twitch chat bot along with additional
    features such as managing OAuth tokens, interacting with Spotify for music playback,
    and storing viewer data in a MongoDB database. Upon initialization, it sets up the
    necessary attributes including the Twitch channel name, OAuth token, Twitch bot prefix,
    Twitch bot token, initial channels to join, EventSub WebSocket client, Spotify client,
    MongoDB client, and viewer data table.

    Attributes:
        channel_name (str): The name of the Twitch channel the bot will operate in.
        oauth_token (str): The OAuth token used for authentication with the Twitch API.
        es_client (eventsub.EventSubWSClient): The EventSub WebSocket client for handling
            Twitch event subscriptions.
        spotify (spotipy.Spotify): The Spotify client for interacting with the Spotify API.
        mongo (motor.motor_asyncio.AsyncIOMotorClient): The MongoDB client for database
            interactions.
        database: The MongoDB database for storing viewer data.
        viewers_table: The MongoDB collection/table for storing viewer data.

    Methods:
        __init__: Initializes the Bot instance with necessary attributes.
        generate_oauth_token_sync: Generates and refreshes the OAuth token synchronously.
        event_token_expired: Refreshes the OAuth token asynchronously when it expires.
        event_ready: Executes code upon confirmation that the bot is ready.

    Usage:
        bot = Bot(channel_name="riddlerrr")
    """

    BOT_NAME = "riddlerrrbot"

    def __init__(self, channel_name: str, prefix: str = "!"):
        """
        Initializes the Bot instance with necessary attributes.

        This method is the constructor of the Bot class. It initializes the bot instance with
        essential attributes such as the Twitch channel name, OAuth token, Twitch bot prefix,
        Twitch bot token, initial channels to join, Spotify client, MongoDB client, and
        viewer data table.

        Args:
            channel_name (str): The name of the Twitch channel the bot will operate in.
            prefix (str, optional): The prefix to identify bot commands in the Twitch chat.
            Defaults to "!".

        Returns:
            None

        Raises:
            None: This method does not raise any exceptions.

        Example:
            bot = Bot(channel_name="riddlerrr")
        """

        self.channel_name: str = channel_name

        self.channel = ChannelInfo(channel_name=channel_name)

        self.user_oauth_token: str = self.generate_oauth_token_sync("user")

        self.bot_oauth_token: str = self.generate_oauth_token_sync("bot")

        super().__init__(
            token=self.bot_oauth_token,
            prefix=prefix,
            initial_channels=[self.channel.channel_name],
        )

        self.mongo = motor.motor_asyncio.AsyncIOMotorClient(
            f"mongodb+srv://{keyring.get_password('mongo_db','username')}:{keyring.get_password('mongo_db','password')}@{keyring.get_password('mongo_db','cluster')}.rljcptb.mongodb.net/?retryWrites=true&w=majority&appName={keyring.get_password('mongo_db','app_name')}"
        )

        self.database = self.mongo.viewerdata
        self.viewers_table = self.database.viewerdata

        self.pubsub = pubsub.PubSubPool(self)

        self._load_cogs()

    async def __ainit__(self) -> None:
        await self._initialise_pubsub()

    async def event_token_expired(self) -> str:
        """
        Refreshes the OAuth token asynchronously when it expires.

        This asynchronous method is triggered when the OAuth token expires. It performs
        an asynchronous HTTP POST request to the Twitch OAuth URL to refresh the OAuth
        token using the refresh token. It updates the OAuth token and refresh token
        stored in the keyring. If the request is unsuccessful, it prints a failure message.

        Args:
            None

        Returns:
            str: The new OAuth access token.

        Example:
            oauth_token = await event_token_expired()
        """
        return await self.generate_oauth_token("bot")

    async def event_ready(self) -> None:
        """
        Executes code upon confirmation that the bot is ready.

        This asynchronous method is triggered when the bot successfully connects and is
        ready to start interacting with the Twitch chat. It prints a message indicating
        the bot's logged-in username to the console.

        Args:
            None

        Returns:
            None

        Raises:
            None: This method does not raise any exceptions.

        Example:
            When the bot is ready, it will print a message like "Logged in as | RiddlerrrBOT"
            to the console.
        """
        print(f"Logged in as | {self.nick}")
        self.channel.channel = self.get_channel(self.channel.channel_name)

    async def generate_oauth_token(self, user_or_bot: str) -> str:
        """
        Refreshes the OAuth token asynchronously when it expires.

        This asynchronous method is triggered when the OAuth token expires. It performs
        an asynchronous HTTP POST request to the Twitch OAuth URL to refresh the OAuth
        token using the refresh token. It updates the OAuth token and refresh token
        stored in the keyring. If the request is unsuccessful, it prints a failure message.

        Args:
            None

        Returns:
            str: The new OAuth access token.

        Raises:
            None: This method does not raise any exceptions, but it will print "FAILED"
            if the response status code is not 200.

        Example:
            oauth_token = await event_token_expired()
        """
        async with aiohttp.ClientSession() as session:
            data = {
                "client_id": keyring.get_password("twitch", "bot_client_id"),
                "client_secret": keyring.get_password("twitch", "bot_client_secret"),
                "grant_type": "refresh_token",
                "refresh_token": keyring.get_password(
                    "twitch", f"{user_or_bot}_refresh_token"
                ),
            }
            async with session.post(
                url=config["TWITCH_OAUTH_URL"], data=data, timeout=60
            ) as response:
                if response.status != 200:
                    print("FAILED")
                json_response = await response.json()
                keyring.set_password(
                    "twitch",
                    f"{user_or_bot}_oauth_token",
                    json_response["access_token"],
                )
                keyring.set_password(
                    "twitch",
                    f"{user_or_bot}_refresh_token",
                    json_response["refresh_token"],
                )
        return json_response["access_token"]

    async def auth_fail_hook(self, topics: list[pubsub.Topic]):
        """
        Refreshes the OAuth token asynchronously when it expires.

        This asynchronous method is triggered when the user's OAuth token expires. It performs
        an asynchronous HTTP POST request to the Twitch OAuth URL to refresh the OAuth
        token using the refresh token. It updates the OAuth token and refresh token
        stored in the keyring.

        Args:
            None

        Returns:
            str: The new OAuth access token.

        Example:
            oauth_token = await event_token_expired()
        """
        new_token = await self.generate_oauth_token("user")
        for topic in topics:
            topic.token = new_token

        await self.pubsub.subscribe_topics(topics)

    def generate_oauth_token_sync(self, user_or_bot: str) -> str:
        """
        Generates and refreshes the OAuth token synchronously.

        This method performs a synchronous HTTP POST request to the Twitch OAuth URL to generate
        a new OAuth token using the refresh token. It updates the OAuth token and refresh token
        stored in the keyring. If the request is unsuccessful, it prints a failure message.

        Args:
            None

        Returns:
            str: The new OAuth access token.

        Raises:
            None: This method does not raise any exceptions, but it will print "FAILED"
            if the response status code is not 200.

        Example:
            oauth_token = generate_oauth_token_sync("bot")
                Generates a new OAuth token for the BOT to use
            oauth_token = generate_oauth_token_sync("user")
                Generates a new OAuth token for the BOT to retrieve user/channel data

        """
        data = {
            "client_id": keyring.get_password("twitch", "bot_client_id"),
            "client_secret": keyring.get_password("twitch", "bot_client_secret"),
            "grant_type": "refresh_token",
            "refresh_token": keyring.get_password(
                "twitch", f"{user_or_bot}_refresh_token"
            ),
        }
        with requests.post(
            url=config["TWITCH_OAUTH_URL"], data=data, timeout=60
        ) as response:
            if response.status_code != 200:
                print("FAILED")
            json_response = json.loads(response.content)
            keyring.set_password(
                "twitch", f"{user_or_bot}_oauth_token", json_response["access_token"]
            )
            keyring.set_password(
                "twitch", f"{user_or_bot}_refresh_token", json_response["refresh_token"]
            )
            # print(f"{user_or_bot}: {json_response['access_token']}")
            return json_response["access_token"]

    def _load_cogs(self):
        for cog in [
            "discord_message_logger",
            "fun_commands",
            "channel_point_rewards",
            "mod_commands",
            "spotify",
            "watch_time_tracker",
        ]:
            self.load_module(f"cogs.{cog}")

    async def _initialise_pubsub(self) -> None:
        channel = await self.fetch_channel(self.channel.channel_name)
        self.channel.channel = channel
        self.channel.channel_id = channel.user.id
        topics = [pubsub.channel_points(self.user_oauth_token)[self.channel.channel_id]]
        await self.pubsub.subscribe_topics(topics)


def main() -> None:
    """
    Entry point for the Twitch chat bot application.

    This function initializes a Twitch chat bot instance, handles asynchronous tasks
    such as checking for token expiration and starting a watch time tracker, and
    runs the bot. It also includes exception handling for graceful shutdown on
    keyboard interruption.

    Workflow:
        - Initializes the Bot instance with the specified channel name.
        - Runs the event for checking if the token has expired.
        - Starts the watch time tracker as an asynchronous task.
        - Runs the bot to start listening and responding to messages.

    Args:
        None

    Returns:
        None

    Raises:
        None: This function handles KeyboardInterrupt for graceful shutdown.

    Example:
        if __name__ == "__main__":
            main()
    """
    try:
        bot = Bot(channel_name="riddlerrr")
        bot.loop.run_until_complete(bot.__ainit__())
        bot.run()
    except KeyboardInterrupt:
        ...


if __name__ == "__main__":
    main()
