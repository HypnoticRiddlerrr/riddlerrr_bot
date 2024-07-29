from config import Config
from keyrings.cryptfile.cryptfile import CryptFileKeyring
from twitchio.ext import commands

keyring = CryptFileKeyring()
config = Config("./config.cfg")

with open("./secrets/keyring_password", mode="r", encoding="UTF-8") as file:
    keyring.keyring_key = file.read().strip()


class ModCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="changetitle", aliases=["title"])
    async def change_title(
        self, ctx: commands.Context, *, new_title: str | None
    ) -> None:
        print(new_title)
        if not new_title:
            await ctx.reply("The new title cannot be blank!")
            await ctx.reply('Usage: !title "<new title name>" OR !title New Title Name')
            return


def prepare(bot: commands.Bot) -> None:
    """
    Prepare the bot by adding the MyCog cog.

    This function is called to register the MyCog cog with the provided bot instance.
    It initializes the MyCog class and uses the bot's `add_cog` method to add it to the bot.

    Args:
        bot (commands.Bot): The instance of the bot to which the cog should be added.
    """
    bot.add_cog(ModCommands(bot))
