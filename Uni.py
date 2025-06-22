import discord
from discord.ext import commands
from discord import app_commands

BANNED_USER_ID = 1282337798765936712  # The user ID to ban
ALLOWED_USER_ID = 1282337798765936712  # Replace with the user ID allowed to use this command

class Uni(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="banlisted", description="Ban the user ID listed in the code")
    async def banlisted(self, interaction: discord.Interaction, reason: str = "No reason provided"):
        if interaction.user.id != ALLOWED_USER_ID:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        try:
            user = await self.bot.fetch_user(BANNED_USER_ID)
            await interaction.guild.ban(user, reason=reason)
            await interaction.response.send_message(f"Banned user `{user}` (ID: {BANNED_USER_ID}).", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to ban user ID {BANNED_USER_ID}: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Uni(bot))