import discord
from discord.ext import commands
from discord import app_commands


class ServerStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="serverstats", description="Show server statistics")
    async def serverstats(self, interaction: discord.Interaction):
        guild = interaction.guild
        total_members = guild.member_count
        online_members = sum(1 for m in guild.members if m.status != discord.Status.offline)
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        roles = len(guild.roles)

        embed = discord.Embed(
            title=f"Server Statistics for {guild.name}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
        embed.add_field(name="Total Members", value=total_members)
        embed.add_field(name="Online Members", value=online_members)
        embed.add_field(name="Text Channels", value=text_channels)
        embed.add_field(name="Voice Channels", value=voice_channels)
        embed.add_field(name="Roles", value=roles)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerStats(bot))