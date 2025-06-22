import discord
from discord.ext import commands
import json
import os

SETTINGS_FILE = "welcome_settings.json"

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "w") as f:
            json.dump({}, f)
    with open(SETTINGS_FILE, "r") as f:
        return json.load(f)

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = load_settings()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setwelcome(self, ctx, channel: discord.TextChannel, *, message: str = None):
        """Set the welcome channel and optional message for this server."""
        guild_id = str(ctx.guild.id)
        self.settings[guild_id] = {
            "channel_id": channel.id,
            "welcome_message": message or "👋 Welcome to the server, {member}!"
        }
        save_settings(self.settings)
        await ctx.send(f"Welcome channel set to {channel.mention}.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setgoodbye(self, ctx, channel: discord.TextChannel, *, message: str = None):
        """Set the goodbye channel and optional message for this server."""
        guild_id = str(ctx.guild.id)
        if guild_id not in self.settings:
            self.settings[guild_id] = {}
        self.settings[guild_id]["goodbye_channel_id"] = channel.id
        self.settings[guild_id]["goodbye_message"] = message or "👋 Goodbye, {member}. We hope to see you again!"
        save_settings(self.settings)
        await ctx.send(f"Goodbye channel set to {channel.mention}.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = str(member.guild.id)
        settings = self.settings.get(guild_id)
        if settings and "channel_id" in settings:
            channel = member.guild.get_channel(settings["channel_id"])
            if channel:
                msg = settings.get("welcome_message", "👋 Welcome to the server, {member}!")
                await channel.send(msg.format(member=member.mention))

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild_id = str(member.guild.id)
        settings = self.settings.get(guild_id)
        channel_id = settings.get("goodbye_channel_id") if settings else None
        if channel_id:
            channel = member.guild.get_channel(channel_id)
            if channel:
                msg = settings.get("goodbye_message", "👋 Goodbye, {member}. We hope to see you again!")
                await channel.send(msg.format(member=member.mention))

async def setup(bot):
    await bot.add_cog(Welcome(bot))