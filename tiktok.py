import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
import os
import json

SETTINGS_FILE = "tiktok_settings.json"

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "w") as f:
            json.dump({}, f)
    with open(SETTINGS_FILE, "r") as f:
        return json.load(f)

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

class TikTokIntegration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = load_settings()
        self.last_video = {}  # {guild_id: {username: last_video_id}}
        self.check_tiktok.start()

    def cog_unload(self):
        self.check_tiktok.cancel()

    @app_commands.command(name="settiktokalert", description="Set up TikTok alerts for this server")
    @app_commands.describe(tiktok_username="TikTok username", discord_channel="Discord channel for alerts")
    @app_commands.checks.has_permissions(administrator=True)
    async def settiktokalert(self, interaction: discord.Interaction, tiktok_username: str, discord_channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.settings:
            self.settings[guild_id] = []
        self.settings[guild_id] = [entry for entry in self.settings[guild_id] if entry["tiktok_username"].lower() != tiktok_username.lower()]
        self.settings[guild_id].append({
            "tiktok_username": tiktok_username.lower(),
            "discord_channel_id": discord_channel.id
        })
        save_settings(self.settings)
        await interaction.response.send_message(f"TikTok alerts for `{tiktok_username}` will be sent to {discord_channel.mention}.", ephemeral=True)

    @app_commands.command(name="removetiktokalert", description="Remove a TikTok alert for this server")
    @app_commands.describe(tiktok_username="TikTok username")
    @app_commands.checks.has_permissions(administrator=True)
    async def removetiktokalert(self, interaction: discord.Interaction, tiktok_username: str):
        guild_id = str(interaction.guild.id)
        if guild_id in self.settings:
            before = len(self.settings[guild_id])
            self.settings[guild_id] = [entry for entry in self.settings[guild_id] if entry["tiktok_username"].lower() != tiktok_username.lower()]
            save_settings(self.settings)
            if len(self.settings[guild_id]) < before:
                await interaction.response.send_message(f"TikTok alert for `{tiktok_username}` removed.", ephemeral=True)
            else:
                await interaction.response.send_message(f"No alert found for `{tiktok_username}`.", ephemeral=True)
        else:
            await interaction.response.send_message(f"No alert found for `{tiktok_username}`.", ephemeral=True)

    @tasks.loop(minutes=2)
    async def check_tiktok(self):
        for guild_id, alerts in self.settings.items():
            for entry in alerts:
                username = entry["tiktok_username"]
                discord_channel_id = entry["discord_channel_id"]
                url = f"https://www.tikwm.com/api/user/posts?unique_id={username}&count=1"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        data = await resp.json()
                        if data.get("data") and data["data"].get("videos"):
                            video = data["data"]["videos"][0]
                            video_id = video["id"]
                            # Check if this is a new video
                            if guild_id not in self.last_video:
                                self.last_video[guild_id] = {}
                            last_id = self.last_video[guild_id].get(username)
                            if last_id != video_id:
                                self.last_video[guild_id][username] = video_id
                                channel = self.bot.get_channel(discord_channel_id)
                                if channel:
                                    video_url = f"https://www.tiktok.com/@{username}/video/{video_id}"
                                    await channel.send(
                                        f"🎬 **New TikTok video by {username}!**\n{video_url}\nCaption: {video.get('title', '')}"
                                    )

    @check_tiktok.before_loop
    async def before_check_tiktok(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(TikTokIntegration(bot))