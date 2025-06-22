import discord
from discord.ext import commands
from discord import app_commands
import json
import os

LOG_SETTINGS_FILE = "log_settings.json"

def load_log_settings():
    if not os.path.exists(LOG_SETTINGS_FILE):
        with open(LOG_SETTINGS_FILE, "w") as f:
            json.dump({}, f)
    with open(LOG_SETTINGS_FILE, "r") as f:
        return json.load(f)

def save_log_settings(settings):
    with open(LOG_SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = load_log_settings()

    @app_commands.command(name="setlogchannel", description="Set the log channel for this server")
    @app_commands.describe(channel="Channel to log events in")
    @app_commands.checks.has_permissions(administrator=True)
    async def setlogchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        self.settings[guild_id] = channel.id
        save_log_settings(self.settings)
        await interaction.response.send_message(f"Log channel set to {channel.mention}.", ephemeral=True)

    async def send_log(self, guild, embed):
        channel_id = self.settings.get(str(guild.id))
        if channel_id:
            channel = guild.get_channel(channel_id)
            if channel:
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.guild and not message.author.bot:
            embed = discord.Embed(
                title="🗑️ Message Deleted",
                description=message.content or "*(empty)*",
                color=discord.Color.red()
            )
            embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
            embed.add_field(name="Channel", value=message.channel.mention)
            await self.send_log(message.guild, embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.guild and not before.author.bot and before.content != after.content:
            embed = discord.Embed(
                title="✏️ Message Edited",
                color=discord.Color.orange()
            )
            embed.set_author(name=str(before.author), icon_url=before.author.display_avatar.url)
            embed.add_field(name="Channel", value=before.channel.mention)
            embed.add_field(name="Before", value=before.content or "*(empty)*", inline=False)
            embed.add_field(name="After", value=after.content or "*(empty)*", inline=False)
            await self.send_log(before.guild, embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        embed = discord.Embed(
            title="✅ Member Joined",
            description=f"{member.mention} ({member})",
            color=discord.Color.green()
        )
        await self.send_log(member.guild, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        embed = discord.Embed(
            title="❌ Member Left",
            description=f"{member.mention} ({member})",
            color=discord.Color.red()
        )
        await self.send_log(member.guild, embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        embed = discord.Embed(
            title="🔨 Member Banned",
            description=f"{user.mention} ({user})",
            color=discord.Color.dark_red()
        )
        await self.send_log(guild, embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        embed = discord.Embed(
            title="⚖️ Member Unbanned",
            description=f"{user.mention} ({user})",
            color=discord.Color.blue()
        )
        await self.send_log(guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        embed = discord.Embed(
            title="📁 Channel Created",
            description=f"{channel.mention} ({channel.name})",
            color=discord.Color.green()
        )
        await self.send_log(channel.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        embed = discord.Embed(
            title="🗑️ Channel Deleted",
            description=f"{channel.name}",
            color=discord.Color.red()
        )
        await self.send_log(channel.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if before.name != after.name:
            embed = discord.Embed(
                title="✏️ Channel Renamed",
                description=f"{before.name} ➔ {after.name}",
                color=discord.Color.orange()
            )
            await self.send_log(after.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        embed = discord.Embed(
            title="➕ Role Created",
            description=f"{role.mention} ({role.name})",
            color=discord.Color.green()
        )
        await self.send_log(role.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        embed = discord.Embed(
            title="➖ Role Deleted",
            description=f"{role.name}",
            color=discord.Color.red()
        )
        await self.send_log(role.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        if before.name != after.name:
            embed = discord.Embed(
                title="✏️ Role Renamed",
                description=f"{before.name} ➔ {after.name}",
                color=discord.Color.orange()
            )
            await self.send_log(after.guild, embed)

async def setup(bot):
    await bot.add_cog(Logging(bot))