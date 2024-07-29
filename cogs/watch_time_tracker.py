import asyncio

import motor
import motor.motor_asyncio
from config import Config
from keyrings.cryptfile.cryptfile import CryptFileKeyring
from twitchio.ext import commands

keyring = CryptFileKeyring()
config = Config("./config.cfg")

with open("./secrets/keyring_password", mode="r", encoding="UTF-8") as file:
    keyring.keyring_key = file.read().strip()


class WatchTimeTracker(commands.Cog):

    def __init__(
        self,
        bot: commands.Bot,
        bot_name: str = "riddlerrrbot",
        channel_name: str = "riddlerrr",
    ):
        self.bot: commands.Bot = bot
        self.bot_name: str = bot_name
        self.channel_name: str = channel_name

        self.bot_list = [
            "regressz",
            "8roe",
            "drapsnatt",
            "d0nk7",
            "8hvdes",
            "markzynk",
            "tarsai",
        ]

        self.mongo = motor.motor_asyncio.AsyncIOMotorClient(
            f"mongodb+srv://{keyring.get_password('mongo_db','username')}:{keyring.get_password('mongo_db','password')}@{keyring.get_password('mongo_db','cluster')}.rljcptb.mongodb.net/?retryWrites=true&w=majority&appName={keyring.get_password('mongo_db','app_name')}"
        )

        self.database = self.mongo.viewerdata
        self.viewers_table = self.database.viewerdata

    @commands.command(aliases=["watchtime", "WATCHTIME"])
    async def watch_time(self, ctx: commands.Context) -> None:
        """
        Displays the total watch time for a user in the Twitch chat.

        This asynchronous method is triggered when a user types '!watchtime' or its alias '!WATCHTIME'
        in the Twitch chat. It retrieves the total watch time for the user from the database and sends
        a message in the chat displaying the watch time in hours and minutes. If no data is found for
        the user, it sends a message indicating this.

        Args:
            ctx (commands.Context): The context of the command message that triggered
            this function. This includes information about the channel, user, and other
            context-specific data.

        Returns:
            None

        Raises:
            None: This method does not raise any exceptions.

        Example:
            !watchtime
            !WATCHTIME
        """
        user = await ctx.author.user()
        viewer_data = await self.viewers_table.find_one({"_id": user.id})
        if not viewer_data:
            await ctx.reply("No data found!")
            return
        watch_time_mins = viewer_data["watch_time_mins"]
        await ctx.reply(
            f"You have been watching for {watch_time_mins//60} hours and {watch_time_mins%60} minutes! (logged since 2024-04-03)"
        )

    @commands.command(aliases=["topwatchers", "TOPWATCHERS"])
    async def top_watchers(self, ctx: commands.Context) -> None:
        cursor = self.viewers_table.find({"watch_time_mins": {"$exists": True}}).sort(
            [("watch_time_mins", -1)]
        )
        viewers = await cursor.to_list(length=5)
        loop_counter = 0
        message = ""
        for viewer in viewers:
            loop_counter += 1
            message += f"{loop_counter}. {viewer['name']} - {(viewer['watch_time_mins']//60)}h, {viewer['watch_time_mins']%60}m"
            if loop_counter < 5:
                message += " | "

        await ctx.reply(message)

    async def start_watch_time_tracker(self) -> None:
        """
        Starts the watch time tracker for a Twitch channel.

        This asynchronous method initiates the watch time tracking process for the channel.
        It waits for 5 seconds before starting the tracking loop. In each iteration of the loop,
        it attempts to update the watch times for viewers in the channel by calling the
        `_update_watch_times` method. The loop runs indefinitely, pausing for 60 seconds
        between each update.

        Args:
            None

        Returns:
            None

        Raises:
            None: Any exceptions raised during the execution of `_update_watch_times` are
            caught and ignored.

        Example:
            await self.start_watch_time_tracker()
        """
        await asyncio.sleep(5)
        while True:
            try:
                asyncio.create_task(self._update_watch_times(self.channel_name))
            finally:
                ...
            await asyncio.sleep(60)

    async def _update_watch_times(self, channel_name: str) -> None:
        """
        Updates the watch times for viewers in a specified Twitch channel.

        This asynchronous method fetches the stream information for the given channel,
        retrieves the list of chatters, and updates the watch time for each viewer
        in the database. If the viewer is not already in the database, a new entry
        is created. Otherwise, the watch time is incremented.

        Args:
            channel_name (str): The name of the Twitch channel to update watch times for.

        Returns:
            None

        Raises:
            None: This method does not raise any exceptions.

        Example:
            await self._update_watch_times("riddlerrr")
        """
        stream_info = await self.bot.fetch_streams(user_logins=[channel_name])
        if not stream_info:
            return

        channel = self.bot.get_channel(channel_name)
        chatters = channel.chatters.copy()
        for chatter in chatters:
            if chatter.name in (channel_name, self.bot_name) or chatter.name in (
                self.bot_list
            ):
                continue
            viewer = await chatter.user()
            viewer_name = chatter.name
            viewer_id = viewer.id

            table_entry = await self.viewers_table.find_one({"_id": viewer_id})

            if not table_entry:
                await self.viewers_table.insert_one(
                    {"_id": viewer_id, "name": viewer_name, "watch_time_mins": 1}
                )
                continue
            await self.viewers_table.update_one(
                {"_id": viewer_id},
                {"$set": {"name": viewer_name}, "$inc": {"watch_time_mins": 1}},
            )


def prepare(bot: commands.Bot) -> None:
    """
    Prepare the bot by adding the MyCog cog.

    This function is called to register the MyCog cog with the provided bot instance.
    It initializes the MyCog class and uses the bot's `add_cog` method to add it to the bot.

    Args:
        bot (commands.Bot): The instance of the bot to which the cog should be added.
    """
    watch_time_tracker = WatchTimeTracker(bot)
    bot.add_cog(watch_time_tracker)
    bot.loop.create_task(watch_time_tracker.start_watch_time_tracker())
