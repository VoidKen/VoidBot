import discord
from discord.ext import commands
import asyncio
from collections import defaultdict

class AntiNuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.deletion_counts = defaultdict(list)  # {user_id: [timestamps]}

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        guild = channel.guild
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            user = entry.user
            now = asyncio.get_event_loop().time()
            self.deletion_counts[user.id] = [
                t for t in self.deletion_counts[user.id] if now - t < 10
            ]  # Keep only deletions in the last 10 seconds
            self.deletion_counts[user.id].append(now)
            if len(self.deletion_counts[user.id]) >= 3:  # Threshold: 3 deletions in 10 seconds
                try:
                    await guild.ban(user, reason="Anti-nuke: Mass channel deletion detected")
                    await guild.owner.send(f"{user} was banned for mass channel deletion.")
                except Exception as e:
                    print(f"Failed to ban {user}: {e}")

async def setup(bot):
    await bot.add_cog(AntiNuke(bot))