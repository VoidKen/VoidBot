import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp as youtube_dl
import asyncio
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials



SPOTIFY_CLIENT_ID = "bcde7425fb5746f7812d5da5d00d57c4"
SPOTIFY_CLIENT_SECRET = "fb330cebf8da42d1bc5883371b52202c"

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))
ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = []

    async def play_next_song(self, voice_channel):
        if self.song_queue:
            next_song = self.song_queue.pop(0)
            filename = await YTDLSource.from_url(next_song, loop=self.bot.loop)
            voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename), after=lambda e: self.bot.loop.create_task(self.play_next_song(voice_channel)))
            await voice_channel.guild.system_channel.send(f'**Now playing:** {filename}')
        else:
            await voice_channel.guild.system_channel.send("The queue is empty.")
    async def spotify_to_youtube(self, url):
        if "track" in url:
            track = sp.track(url)
            query = f"ytsearch1:{track['name']} {track['artists'][0]['name']}"
            # yt-dlp will return the first search result
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))
            if 'entries' in data and data['entries']:
                return data['entries'][0]['webpage_url']
        return None
        return None 
    @app_commands.command(name='join', description='Tells the bot to join the voice channel')
    async def join(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            await interaction.response.send_message(f"{interaction.user.name} is not connected to a voice channel")
            return
        else:
            channel = interaction.user.voice.channel
        await channel.connect()
        await interaction.response.send_message(f"Joined {channel.name}")

    @app_commands.command(name='leave', description='To make the bot leave the voice channel')
    async def leave(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
            await interaction.response.send_message("Left the voice channel")
        else:
            await interaction.response.send_message("The bot is not connected to a voice channel.")

    @app_commands.command(name='play_song', description='To play song')
    @app_commands.describe(url="The URL of the song to play")
    async def play_song(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()  # Defer immediately!

        # Spotify support
        if "open.spotify.com/track" in url:
            yt_url = await self.spotify_to_youtube(url)
            if yt_url:
                url = yt_url
            else:
                await interaction.followup.send("Could not find this Spotify track on YouTube.")
                return

        server = interaction.guild
        voice_channel = server.voice_client

        if not voice_channel:
            if interaction.user.voice:
                channel = interaction.user.voice.channel
                await channel.connect()
                voice_channel = server.voice_client
            else:
                await interaction.followup.send("You need to be in a voice channel to play music.")
                return

        self.song_queue.append(url)
        await interaction.followup.send(f"Added to queue: {url}")

        if not voice_channel.is_playing():
            await self.play_next_song(voice_channel)

    @app_commands.command(name='pause', description='This command pauses the song')
    async def pause(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await interaction.response.send_message("Paused the song")
        else:
            await interaction.response.send_message("The bot is not playing anything at the moment.")

    @app_commands.command(name='resume', description='Resumes the song')
    async def resume(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await interaction.response.send_message("Resumed the song")
        else:
            await interaction.response.send_message("The bot was not playing anything before this. Use play_song command")

    @app_commands.command(name='stop', description='Stops the song')
    async def stop(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            self.song_queue.clear()
            await interaction.response.send_message("Stopped the song and cleared the queue")
        else:
            await interaction.response.send_message("The bot is not playing anything at the moment.")

    @app_commands.command(name='add_to_queue', description='Add a song to the queue')
    @app_commands.describe(url="The URL of the song to add")
    async def add_to_queue(self, interaction: discord.Interaction, url: str):
        # Spotify support
        if "open.spotify.com/track" in url:
            yt_url = await self.spotify_to_youtube(url)
            if yt_url:
                url = yt_url
            else:
                await interaction.response.send_message("Could not find this Spotify track on YouTube.")
                return
        self.song_queue.append(url)
        await interaction.response.send_message(f"Added {url} to the queue")

    @app_commands.command(name='view_queue', description='View the current song queue')
    async def view_queue(self, interaction: discord.Interaction):
        if self.song_queue:
            queue_list = "\n".join([f"{i+1}. {url}" for i, url in enumerate(self.song_queue)])
            await interaction.response.send_message(f"Current queue:\n{queue_list}")
        else:
            await interaction.response.send_message("The queue is empty")

    @app_commands.command(name='skip', description='Skip the currently playing song')
    async def skip(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await interaction.response.send_message("Skipped the song")
            await self.play_next_song(voice_client)
        else:
            await interaction.response.send_message("The bot is not playing anything at the moment")

    @app_commands.command(name='clear_queue', description='Clear the song queue')
    async def clear_queue(self, interaction: discord.Interaction):
        self.song_queue.clear()
        await interaction.response.send_message("Cleared the queue")

    @app_commands.command(name='volume', description='Change the volume of the music')
    @app_commands.describe(volume="The volume level (0-100)")
    async def volume(self, interaction: discord.Interaction, volume: int):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            if 0 <= volume <= 100:
                voice_client.source.volume = volume / 100
                await interaction.response.send_message(f"Volume set to {volume}%")
            else:
                await interaction.response.send_message("Volume must be between 0 and 100")
        else:
            await interaction.response.send_message("The bot is not playing anything at the moment.")

async def setup(bot):
    await bot.add_cog(Music(bot))