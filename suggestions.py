import discord
from discord.ext import commands
from discord import app_commands
import json
import os

SUGGESTIONS_FILE = "suggestions_settings.json"

def load_settings():
    if not os.path.exists(SUGGESTIONS_FILE):
        with open(SUGGESTIONS_FILE, "w") as f:
            json.dump({}, f)
    with open(SUGGESTIONS_FILE, "r") as f:
        return json.load(f)

def save_settings(settings):
    with open(SUGGESTIONS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = load_settings()

    @app_commands.command(name="setsuggestions", description="Set the suggestions channel for this server")
    @app_commands.describe(channel="Channel to post suggestions in")
    @app_commands.checks.has_permissions(administrator=True)
    async def setsuggestions(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        self.settings[guild_id] = channel.id
        save_settings(self.settings)
        await interaction.response.send_message(f"Suggestions channel set to {channel.mention}.", ephemeral=True)

    @app_commands.command(name="suggest", description="Submit a server suggestion")
    @app_commands.describe(suggestion="Your suggestion")
    async def suggest(self, interaction: discord.Interaction, suggestion: str):
        guild_id = str(interaction.guild.id)
        channel_id = self.settings.get(guild_id)
        if not channel_id:
            await interaction.response.send_message("Suggestions channel is not set for this server.", ephemeral=True)
            return
        channel = interaction.guild.get_channel(channel_id)
        if not channel:
            await interaction.response.send_message("Suggestions channel not found.", ephemeral=True)
            return
        embed = discord.Embed(
            title="New Suggestion",
            description=suggestion,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Suggested by {interaction.user}", icon_url=interaction.user.display_avatar.url)
        msg = await channel.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        await interaction.response.send_message("Your suggestion has been submitted!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Suggestions(bot))