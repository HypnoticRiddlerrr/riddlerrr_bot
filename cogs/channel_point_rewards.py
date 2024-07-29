"""
This module defines a cog for handling specific channel interactions and events for a Twitch bot.

The FunChannelCommands cog includes event handlers and commands that interact with the
Twitch channel in fun and engaging ways. Currently, it includes functionality for responding
to custom channel point rewards by presenting riddles to viewers.

Classes:
    FunChannelCommands(commands.Cog): A cog that includes event handling for messages and
    commands for fetching and presenting riddles.

Functions:
    prepare(bot: commands.Bot) -> None:
        Adds the FunChannelCommands cog to the bot instance.

Usage:
    Load this cog in your main bot file to add channel-specific interaction commands to your bot's
    functionality. Example:

    bot.load_module('cogs.fun_channel_commands')
"""

import asyncio
import json
import random

import aiohttp
from config import Config
from keyrings.cryptfile.cryptfile import CryptFileKeyring
from twitchio import Message
from twitchio.ext import commands, pubsub

from utils.dataclasses import CoinflipPrediction

keyring = CryptFileKeyring()
config = Config("./config.cfg")

with open("./secrets/keyring_password", mode="r", encoding="UTF-8") as file:
    keyring.keyring_key = file.read().strip()


class ChannelPointRewards(commands.Cog):
    """
    A set of commands and event handlers specific to channel interactions for the Twitch bot.

    This cog contains commands that are triggered by channel events such as receiving a message.
    It includes functionality for responding to custom channel point rewards with riddles.

    Attributes:
        bot (commands.Bot): The instance of the bot.

    Methods:
        event_message(message: Message) -> None:
            Handles incoming messages and triggers specific actions based on custom rewards.

        get_a_riddle(ctx: commands.Context) -> None:
            Fetches a riddle from an external API and manages the timing for the response.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.event()
    async def event_message(self, message: Message):
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
            return
        if "custom-reward-id" in message.tags:
            match message.tags["custom-reward-id"]:
                case "3021857f-d329-4de0-85ff-b557375849f5":  # Get a riddle
                    await self.get_a_riddle(
                        commands.Context(
                            prefix=None,
                            content=message.content,
                            message=message,
                            bot=self,
                        )
                    )

    @commands.Cog.event()
    async def event_pubsub_channel_points(
        self, event: pubsub.PubSubChannelPointsMessage
    ):
        match event.reward.id:
            case "eadc734f-390c-4795-87d2-04b538e3afb7":
                await self.create_coin_flip_prediction()

    async def create_coin_flip_prediction(self) -> None:
        response_heads_id: str | None = None
        response_tails_id: str | None = None
        request_headers = {
            "Authorization": f"Bearer {keyring.get_password(service='twitch', username='user_oauth_token')}",
            "Client-Id": keyring.get_password("twitch", "bot_client_id"),
            "Content-Type": "application/json",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=config["TWITCH_PREDICTION_URL"],
                headers=request_headers,
                data=json.dumps(
                    {
                        "broadcaster_id": self.bot.channel.channel_id,
                        "title": "Heads or Tails?",
                        "outcomes": [{"title": "Heads"}, {"title": "Tails"}],
                        "prediction_window": 60,
                    }
                ),
            ) as response:
                response_json = await response.json()
                if response.status != 200:
                    if response_json["message"] and (
                        response_json["message"]
                        == "prediction event already active, only one allowed at a time"
                    ):
                        await self.bot.channel.channel.send(
                            "A prediction is already underway!"
                        )
                    else:
                        await self.bot.channel.channel.send(
                            "An error occurred because @Riddlerrr cannot make a good bot. 🙃"
                        )
                        return
                prediction_data = response_json["data"][0]
                for outcome in prediction_data["outcomes"]:
                    if outcome["title"].lower() == "heads":
                        response_heads_id = outcome["id"]
                    elif outcome["title"].lower() == "tails":
                        response_tails_id = outcome["id"]
            ongoing_coinflip_prediction = CoinflipPrediction(
                prediction_id=prediction_data["id"],
                heads_id=response_heads_id,
                tails_id=response_tails_id,
            )
            await asyncio.sleep(60)
            result = random.choice(["Heads", "Tails"])
            match result.lower():
                case "heads":
                    outcome_id = ongoing_coinflip_prediction.heads_id
                case "tails":
                    outcome_id = ongoing_coinflip_prediction.tails_id
            async with session.patch(
                url=f"https://api.twitch.tv/helix/predictions?broadcaster_id={self.bot.channel.channel_id}&id={ongoing_coinflip_prediction.prediction_id}&status=RESOLVED&winning_outcome_id={outcome_id}",
                headers={
                    "Authorization": f"Bearer {keyring.get_password(service='twitch', username='user_oauth_token')}",
                    "Client-Id": keyring.get_password("twitch", "bot_client_id"),
                },
            ) as response:
                await self.bot.channel.channel.send(f"The result is {result}!")

    async def get_a_riddle(self, ctx: commands.Context) -> None:
        """
        Retrieves and sends a riddle to the Twitch chat when a channel points reward is redeemed.

        This asynchronous method is triggered when a user redeems a specific channel points reward
        in the Twitch chat. It fetches a riddle from the API Ninjas Riddles API and sends the riddle
        question to the chat. The method waits for 30 seconds before revealing the answer to the riddle.

        Args:
            message (commands.Context): The context of the command message that triggered
            this function. This includes information about the channel, user, and other
            context-specific data.

        Returns:
            None

        Raises:
            None: This method does not raise any exceptions.

        Example:
            await self.get_a_riddle(message)
        """
        async with aiohttp.ClientSession() as session:
            riddle_length: int = 501
            answer_length: int = 501
            while riddle_length > 439 and answer_length > 439:
                async with session.get(
                    url="https://riddles-api.vercel.app/random",
                ) as response:
                    json_response = await response.json()
                    riddle = json_response["riddle"]
                    answer = json_response["answer"]
                    riddle_length = len(riddle)
                    answer_length = len(answer)
            await ctx.reply(f"{riddle} You have 30 seconds to guess the answer")
            await asyncio.sleep(30)
            await ctx.reply(f"The answer to your riddle was: {answer}")


def prepare(bot: commands.Bot) -> None:
    """
    Prepare the bot by adding the MyCog cog.

    This function is called to register the MyCog cog with the provided bot instance.
    It initializes the MyCog class and uses the bot's `add_cog` method to add it to the bot.

    Args:
        bot (commands.Bot): The instance of the bot to which the cog should be added.
    """
    bot.add_cog(ChannelPointRewards(bot))
