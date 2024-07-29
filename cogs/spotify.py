"""
This module defines a cog for handling Spotify-related commands and events for a Twitch bot.

The Spotify cog includes functionality for interacting with Spotify, such as adding songs
to a queue and fetching the currently playing song.

Classes:
    Spotify(commands.Cog): A cog that includes commands and event handling related to Spotify.

Functions:
    prepare(bot: commands.Bot) -> None:
        Adds the Spotify cog to the bot instance.

Usage:
    Load this cog in your main bot file to add Spotify-related commands and events to your bot's
    functionality. Example:

    bot.load_module('cogs.spotify')
"""

import spotipy
from config import Config
from keyrings.cryptfile.cryptfile import CryptFileKeyring
from spotipy.oauth2 import SpotifyOAuth
from twitchio import Message
from twitchio.ext import commands

keyring = CryptFileKeyring()
config = Config("./config.cfg")


with open("./secrets/keyring_password", mode="r", encoding="UTF-8") as file:
    keyring.keyring_key = file.read().strip()


class Spotify(commands.Cog):
    """
    A class for handling Spotify-related commands and events for the Twitch bot.

    This cog includes functionality for interacting with Spotify, such as adding songs
    to a queue and fetching the currently playing song.

    Attributes:
        bot (commands.Bot): The instance of the bot.

    Methods:
        event_message(message: Message) -> None:
            Handles incoming messages and triggers specific actions based on custom rewards.

        song(ctx: commands.Context) -> None:
            Retrieves the currently playing song and sends it into the Twitch chat.

        add_song_to_spotify_queue(ctx: commands.Context) -> None:
            Attempts to find the linked song and adds it to the user's queue and Twitch playlist.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.spotify = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=keyring.get_password("spotify", "client_id"),
                client_secret=keyring.get_password("spotify", "client_secret"),
                redirect_uri=config["SPOTIFY_REDIRECT_URL"],
                scope=[
                    "user-modify-playback-state",
                    "user-read-currently-playing",
                    "user-read-playback-state",
                    "playlist-modify-public",
                ],
            )
        )

    @commands.Cog.event()
    async def event_message(self, message: Message):
        """
        Handles actions upon receiving a message in the Twitch chat.

        This asynchronous method processes incoming messages and performs specific actions
        based on the message content and tags. If the message contains a custom reward ID,
        it triggers the corresponding action such as adding a song to the Spotify queue.

        Args:
            message (Message): The message object received from the Twitch chat. This
            includes information about the message content, sender, and any associated tags.

        Returns:
            None

        Raises:
            None: This method does not raise any exceptions.

        Actions:
            - If the message is an echo, it is ignored.
            - If the message contains the custom reward ID for adding a song to the Spotify queue,
            it calls the `add_song_to_spotify_queue` method.

        Example:
            When a user redeems a custom reward with the ID "0f2a93f0-7e7d-4f2c-a667-8bb622783957",
            the bot will add a song to the Spotify queue.
        """
        if message.echo:
            return

        if "custom-reward-id" in message.tags:
            match message.tags["custom-reward-id"]:
                case "0f2a93f0-7e7d-4f2c-a667-8bb622783957":  # Add song to queue redeem
                    await self.add_song_to_spotify_queue(
                        commands.Context(
                            prefix=None,
                            content=message.content,
                            message=message,
                            bot=self,
                        )
                    )

    @commands.command(aliases=["SONG"])
    async def song(self, ctx: commands.Context) -> None:
        """
        Retrieves and sends the currently playing song to the Twitch chat.

        This asynchronous method is triggered when a user types '!song' or its alias '!SONG'
        in the Twitch chat. It fetches the currently playing track from Spotify and sends
        the song name, artist, and a link to the song in the chat. If no song is currently
        playing, it sends a message indicating this.

        Args:
            ctx (commands.Context): The context of the command message that triggered
            this function. This includes information about the channel, user, and other
            context-specific data.

        Returns:
            None

        Raises:
            None: This method does not raise any exceptions.

        Example:
            !song
            !SONG
        """
        current_song = self.spotify.current_user_playing_track()
        if not current_song:
            await ctx.reply("No song currently playing.")
        await ctx.reply(
            f"Currently playing: {current_song['item']['name']} by {current_song['item']['artists'][0]['name']} | {current_song['item']['external_urls']['spotify']}"
        )

    async def add_song_to_spotify_queue(self, message: commands.Context) -> None:
        """
        Adds a song to the Spotify queue when a channel points reward is redeemed.

        This asynchronous method is triggered when a user redeems a specific channel points
        reward in the Twitch chat. It takes a song link from the message content, extracts
        the Spotify URI, and adds the song to the Spotify queue. The method responds in the
        chat with the song details or an error message if the song cannot be found. Finally
        it adds the song to the Twitch Requests playlist on Spotify

        Args:
            message (commands.Context): The context of the command message that triggered
            this function. This includes information about the channel, user, and other
            context-specific data.

        Returns:
            None

        Raises:
            None: This method handles exceptions internally and does not raise any exceptions.

        Example:
            await self.add_song_to_spotify_queue(message)
        """
        song_link = message.message.content
        try:
            spotify_uri = song_link.split("/")[-1].split("?")[0]
            track_info = self.spotify.track(track_id=spotify_uri, market=None)
            self.spotify.add_to_queue(spotify_uri)
            await message.reply(
                f"Added {track_info['name']} by {track_info['artists'][0]['name']} to the queue."
            )
        except spotipy.SpotifyException:
            await message.reply("Unable to find the song you have linked.")
            await message.channel.send(f"/delete {message.message.tags['id']}")
        finally:
            user = self.spotify.current_user()
            self.spotify.user_playlist_add_tracks(
                user, "3owpEcSp6cxE7VtXB6OgHG", [spotify_uri]
            )


def prepare(bot: commands.Bot) -> None:
    """
    Prepare the bot by adding the MyCog cog.

    This function is called to register the MyCog cog with the provided bot instance.
    It initializes the MyCog class and uses the bot's `add_cog` method to add it to the bot.

    Args:
        bot (commands.Bot): The instance of the bot to which the cog should be added.
    """
    bot.add_cog(Spotify(bot))
