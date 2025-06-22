import discord
from discord.ext import commands
from discord import app_commands
import json
import os

def load_levels():
    if os.path.exists(LEVELS_FILE):
        try:
            with open(LEVELS_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # Auto-fix: reset to empty dict if file is corrupt
            with open(LEVELS_FILE, "w") as f:
                json.dump({}, f)
            return {}
    return {}

LEVELS_FILE = "levels.json"

def load_levels():
    if os.path.exists(LEVELS_FILE):
        with open(LEVELS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_levels(levels):
    with open(LEVELS_FILE, "w") as f:
        json.dump(levels, f)

class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.levels = load_levels()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        user_id = str(message.author.id)
        if user_id not in self.levels:
            self.levels[user_id] = {"xp": 0, "level": 1}

        self.levels[user_id]["xp"] += 10
        if self.levels[user_id]["xp"] >= self.levels[user_id]["level"] * 100:
            self.levels[user_id]["xp"] = 0
            self.levels[user_id]["level"] += 1
            await message.channel.send(f"Congratulations {message.author.mention}, you leveled up to level {self.levels[user_id]['level']}!")

        save_levels(self.levels)

    @app_commands.command(name="level", description="Check your level")
    async def level(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        if user_id in self.levels:
            level = self.levels[user_id]["level"]
            xp = self.levels[user_id]["xp"]
            await interaction.response.send_message(f"You are level {level} with {xp} XP.")
        else:
            await interaction.response.send_message("You have no levels yet.")

    @app_commands.command(name="leaderboard", description="Show the top users by level")
    async def leaderboard(self, interaction: discord.Interaction):
        sorted_levels = sorted(self.levels.items(), key=lambda x: x[1]["level"], reverse=True)
        leaderboard_message = "\n".join([f"{i+1}. <@{user_id}> - Level {data['level']}" for i, (user_id, data) in enumerate(sorted_levels[:10])])
        await interaction.response.send_message(f"**Leaderboard**\n{leaderboard_message}")

    @app_commands.command(name="set_xp", description="Set the XP for a user")
    @app_commands.describe(member="The member to set XP for", xp="The amount of XP to set")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_xp(self, interaction: discord.Interaction, member: discord.Member, xp: int):
        user_id = str(member.id)
        if user_id in self.levels:
            self.levels[user_id]["xp"] = xp
            save_levels(self.levels)
            await interaction.response.send_message(f"Set {member.mention}'s XP to {xp}.")
        else:
            await interaction.response.send_message(f"{member.mention} has no levels yet.")

    @app_commands.command(name="set_level", description="Set the level for a user")
    @app_commands.describe(member="The member to set level for", level="The level to set")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_level(self, interaction: discord.Interaction, member: discord.Member, level: int):
        user_id = str(member.id)
        if user_id in self.levels:
            self.levels[user_id]["level"] = level
            save_levels(self.levels)
            await interaction.response.send_message(f"Set {member.mention}'s level to {level}.")
        else:
            await interaction.response.send_message(f"{member.mention} has no levels yet.")

    @app_commands.command(name="user_stats", description="Get detailed user statistics")
    @app_commands.describe(member="The member to get statistics for")
    async def user_stats(self, interaction: discord.Interaction, member: discord.Member):
        user_id = str(member.id)
        if user_id in self.levels:
            level = self.levels[user_id]["level"]
            xp = self.levels[user_id]["xp"]
            await interaction.response.send_message(f"{member.mention} is level {level} with {xp} XP.")
        else:
            await interaction.response.send_message(f"{member.mention} has no levels yet.")

async def setup(bot):
    await bot.add_cog(Level(bot))