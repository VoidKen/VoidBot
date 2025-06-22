import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import random

class Giveaways(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="giveaway", description="Start a timed giveaway")
    @app_commands.describe(
        channel="Channel to host the giveaway in",
        duration="Duration in seconds",
        prize="Prize for the giveaway"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def giveaway(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        duration: int,
        prize: str
    ):
        embed = discord.Embed(
            title="🎉 Giveaway! 🎉",
            description=f"Prize: **{prize}**\nReact with 🎉 to enter!\nEnds in {duration} seconds.",
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Hosted by {interaction.user}")
        msg = await channel.send(embed=embed)
        await msg.add_reaction("🎉")
        await interaction.response.send_message(f"Giveaway started in {channel.mention}!", ephemeral=True)

        await asyncio.sleep(duration)
        msg = await channel.fetch_message(msg.id)
        users = set()
        for reaction in msg.reactions:
            if str(reaction.emoji) == "🎉":
                async for user in reaction.users():
                    if not user.bot:
                        users.add(user)
        if users:
            winner = random.choice(list(users))
            await channel.send(f"🎊 Congratulations {winner.mention}, you won **{prize}**!")
        else:
            await channel.send("No valid entries, no winner this time.")

async def setup(bot):
    await bot.add_cog(Giveaways(bot))