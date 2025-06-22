import discord
from discord.ext import commands
from discord import app_commands
import json
import os

MODMAIL_FILE = "modmail_settings.json"

def load_settings():
    if not os.path.exists(MODMAIL_FILE):
        with open(MODMAIL_FILE, "w") as f:
            json.dump({}, f)
    with open(MODMAIL_FILE, "r") as f:
        return json.load(f)

def save_settings(settings):
    with open(MODMAIL_FILE, "w") as f:
        json.dump(settings, f, indent=2)

class ModMail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = load_settings()

    @app_commands.command(name="setmodmail", description="Set the modmail channel for this server")
    @app_commands.describe(channel="Channel to receive modmail messages")
    @app_commands.checks.has_permissions(administrator=True)
    async def setmodmail(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        self.settings[guild_id] = channel.id
        save_settings(self.settings)
        await interaction.response.send_message(f"Modmail channel set to {channel.mention}.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        # Only handle DMs from users (not bots)
        if message.guild is None and not message.author.bot:
            # Only send to servers where the user is a member
            for guild_id, channel_id in self.settings.items():
                guild = self.bot.get_guild(int(guild_id))
                if guild and guild.get_member(message.author.id):
                    channel = guild.get_channel(channel_id)
                    if channel:
                        embed = discord.Embed(
                            title="📬 New Modmail Message",
                            description=message.content,
                            color=discord.Color.blue()
                        )
                        embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
                        embed.set_footer(text=f"User ID: {message.author.id}")
                        await channel.send(embed=embed)
        # Optionally, handle attachments
        #     if message.attachments:
        #         for att in message.attachments:
        #             await channel.send(att.url)

    @app_commands.command(name="replymodmail", description="Reply to a user's modmail (staff only)")
    @app_commands.describe(user_id="User ID to reply to", message="Your reply message")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def replymodmail(self, interaction: discord.Interaction, user_id: str, message: str):
        try:
            user = await self.bot.fetch_user(int(user_id))
            await user.send(f"📬 **Reply from staff:**\n{message}")
            await interaction.response.send_message("Reply sent!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to send reply: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ModMail(bot))