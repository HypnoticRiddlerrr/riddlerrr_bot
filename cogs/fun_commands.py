"""
This module defines a cog for fun and humorous commands for a Twitch bot.

The FunCommands cog contains various commands intended to entertain and engage
with viewers through playful messages and responses. Each command is designed
to be light-hearted and amusing, providing a fun interaction for users in the
Twitch chat.

Classes:
    FunCommands(commands.Cog): A cog that includes commands like `dick_size` and
    `chips_and_gravy` for humorous interactions.

Functions:
    prepare(bot: commands.Bot) -> None:
        Adds the FunCommands cog to the bot instance.

Usage:
    Load this cog in your main bot file to add the fun commands to your bot's
    functionality. Example:
    
    bot.load_module('cogs.fun_commands')
"""

import asyncio
import datetime
import random

import twitchio
from config import Config
from keyrings.cryptfile.cryptfile import CryptFileKeyring
from twitchio.ext import commands

from configs.fun_commands import PIZZA_TOPPINGS

keyring = CryptFileKeyring()
config = Config("./config.cfg")


with open("./secrets/keyring_password", mode="r", encoding="UTF-8") as file:
    keyring.keyring_key = file.read().strip()


class FunCommands(commands.Cog):
    """
    A set of fun and humorous commands for the Twitch bot.

    This cog contains commands intended to entertain and engage with viewers
    through playful messages and responses.

    Attributes:
        bot (commands.Bot): The instance of the bot.

    Methods:
        dick_size(ctx: commands.Context) -> None:
            Responds with a humorous message about the user's "dick size".

        chips_and_gravy(ctx: commands.Context) -> None:
            Responds with a fixed humorous message related to 'chips and gravy'.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.odds_on_challenges: dict = {}

    @commands.command(aliases=["chipsandgravy", "CHIPSANDGRAVY"])
    async def chips_and_gravy(self, ctx: commands.Context) -> None:
        """
        Responds to the '!chipsandgravy' command with a fun message.

        This asynchronous method is a fun user command triggered when a user types
        '!chipsandgravy' or its alias '!CHIPSANDGRAVY' in the Twitch chat. It replies with
        a predefined message.

        Args:
            ctx (commands.Context): The context of the command message that triggered
            this function. This includes information about the channel, user, and other
            context-specific data.

        Returns:
            None

        Raises:
            None: This method does not raise any exceptions.

        Example:
            !chipsandgravy
            !CHIPSANDGRAVY
        """
        await ctx.reply('rabble_ron: "god save the queen!"')

    @commands.command(aliases=["dicksize", "DICKSIZE"])
    async def dick_size(self, ctx: commands.Context) -> None:
        """
        Generates a random number and returns it in chat as the user's dick size.

        This asynchronous method is a fun command triggered when a user types '!dicksize' or
        its alias '!DICKSIZE' in the Twitch chat. Depending on the user's name, it either
        returns a predefined humorous message or generates a random number to represent the
        user's dick size and sends the result in the chat.

        Args:
            ctx (commands.Context): The context of the command message that triggered
            this function. This includes information about the channel, user, and other
            context-specific data.

        Returns:
            None

        Raises:
            None: This method does not raise any exceptions.

        Example:
            !dicksize
            !DICKSIZE
        """
        match ctx.author.name:
            case "riddlerrr":
                message = "You have the biggest dick in all the land, coming in at 20 inches long! 🍆😏"
            case "quecrad":
                message = "If there is anything we know about Quecrad, it's that he has the nickname 'long dong silver' for a reason. 😏 He won't leak the length though."
            case "ryzaha":
                message = "There's a reason we call him the 'human tripod'. 😬 Packing something the length of his leg! Won't let us measure though. 😩"
            case _:
                dick_size = random.uniform(a=0.001, b=10)
                message = f"Your dick size is {round(dick_size, 2)} inches long."
        await ctx.reply(message)

    @commands.command()
    async def pizza(self, ctx: commands.Context) -> None:
        async def select_random_topping(
            topping_list,
            super_rare_item: str = None,
            rare_probability: int = 0,
        ) -> str:
            probabilities = []

            normal_probability = (1 - rare_probability) / (len(topping_list) - 1)

            for topping in topping_list:
                if topping == super_rare_item:
                    probabilities.append(rare_probability)
                else:
                    probabilities.append(normal_probability)

            total_probability = sum(probabilities)
            probabilities = [
                probability / total_probability for probability in probabilities
            ]

            selected_topping = random.choices(topping_list, weights=probabilities, k=1)[
                0
            ]

            if selected_topping == super_rare_item:
                return selected_topping, True
            return selected_topping, False

        random_sauce, _ = await select_random_topping(PIZZA_TOPPINGS["sauces"])
        random_cheese, _ = await select_random_topping(PIZZA_TOPPINGS["cheese"])
        random_topping_1, topping_1_is_bad = await select_random_topping(
            PIZZA_TOPPINGS["topping_1"],
            super_rare_item="Pineapple",
            rare_probability=0.01,
        )
        random_topping_2, topping_2_is_bad = await select_random_topping(
            PIZZA_TOPPINGS["topping_2"],
            super_rare_item="Mushrooms",
            rare_probability=0.01,
        )

        await ctx.reply(
            f"Your pizza combo is {random_sauce} sauce, {random_cheese} cheese with {random_topping_1} and {random_topping_2}."
        )

        if topping_1_is_bad and topping_2_is_bad:
            await ctx.reply(
                "I literally cannot think of a worse pizza... be gone for 2 hours!"
            )
            return
        if topping_1_is_bad:
            await ctx.reply(
                f"{random_topping_1} is a terrible choice... have 2 minutes to think about what you've done"
            )
            return
        if topping_2_is_bad:
            await ctx.reply(
                f"{random_topping_2} is a terrible choice... have 2 minutes to think about what you've done"
            )
            return

    @commands.command(aliases=["IP", "iP", "Ip"])
    async def ip(self, ctx: commands.Context) -> None:
        await ctx.reply("01:21:D0:1")

    @commands.command(aliases=["bbmpin", "BBPMPIN", "BBM"])
    async def bbm(self, ctx: commands.Context) -> None:
        await ctx.reply("0121DO1")

    @commands.command()
    async def build(self, ctx: commands.Context) -> None:
        await ctx.reply(
            "Last Epoch build: https://maxroll.gg/last-epoch/build-guides/torment-warlock-guide"
        )

    # @commands.command(aliases=["oo", "odds", "oddson"])
    # async def odds_on_challenge(
    #     self,
    #     ctx: commands.Context,
    #     challenger: twitchio.User,
    #     ban_length: str = "1h",
    # ) -> None:
    #     self.odds_on_challenges[challenger.display_name] = {
    #         "time": datetime.datetime.now(),
    #         "ban_length": ban_length,
    #         "requester": ctx.author.display_name,
    #     }

    #     await ctx.reply(
    #         f"Odds on you get muted for {ban_length}? Do !ooaccept <odds> to accept! (Expires in 2 minutes)"
    #     )

    # @commands.command(aliases=["ooaccept", "oddsaccept", "oddsonaccept"])
    # async def odds_on_accept(
    #     self, ctx: commands.Context, chosen_number: int = 100
    # ) -> None:
    #     requester_number = random.randint(1, chosen_number)
    #     challenger_number = random.randint(1, chosen_number)
    #     if requester_number == challenger_number:
    #         await ctx.reply(
    #             f"You both landed on {challenger_number}! See you in {self.odds_on_challenges[ctx.author.display_name]['ban_length']}"
    #         )
    #         # Insert timeout logic here
    #         return
    #     await ctx.reply(
    #         f"@{self.odds_on_challenges[ctx.author.display_name]['requester']} guessed {requester_number} and @{ctx.author.display_name} guessed {challenger_number}. No punishments here. ;)"
    #     )

    # @commands.command(aliases=["oodecline", "oddsdecline", "oddsondecline"])
    # async def odds_on_decline(self, ctx: commands.Context) -> None: ...


def prepare(bot: commands.Bot) -> None:
    """
    Prepare the bot by adding the MyCog cog.

    This function is called to register the MyCog cog with the provided bot instance.
    It initializes the MyCog class and uses the bot's `add_cog` method to add it to the bot.

    Args:
        bot (commands.Bot): The instance of the bot to which the cog should be added.
    """
    bot.add_cog(FunCommands(bot))
