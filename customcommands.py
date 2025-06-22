import discord
from discord.ext import commands
from discord import app_commands
import json
import os

CUSTOM_CMDS_FILE = "custom_commands.json"

def load_commands():
    if not os.path.exists(CUSTOM_CMDS_FILE):
        with open(CUSTOM_CMDS_FILE, "w") as f:
            json.dump({}, f)
    with open(CUSTOM_CMDS_FILE, "r") as f:
        return json.load(f)

def save_commands(cmds):
    with open(CUSTOM_CMDS_FILE, "w") as f:
        json.dump(cmds, f, indent=2)

class CustomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.commands_per_guild = load_commands()

    @app_commands.command(name="addcustom", description="Add a custom command for this server")
    @app_commands.describe(name="Command name", response="Response text")
    @app_commands.checks.has_permissions(administrator=True)
    async def addcustom(self, interaction: discord.Interaction, name: str, response: str):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.commands_per_guild:
            self.commands_per_guild[guild_id] = {}
        self.commands_per_guild[guild_id][name.lower()] = response
        save_commands(self.commands_per_guild)
        await interaction.response.send_message(f"Custom command `/{name}` added!", ephemeral=True)

    @app_commands.command(name="delcustom", description="Delete a custom command for this server")
    @app_commands.describe(name="Command name")
    @app_commands.checks.has_permissions(administrator=True)
    async def delcustom(self, interaction: discord.Interaction, name: str):
        guild_id = str(interaction.guild.id)
        if guild_id in self.commands_per_guild and name.lower() in self.commands_per_guild[guild_id]:
            del self.commands_per_guild[guild_id][name.lower()]
            save_commands(self.commands_per_guild)
            await interaction.response.send_message(f"Custom command `/{name}` deleted.", ephemeral=True)
        else:
            await interaction.response.send_message("That custom command does not exist.", ephemeral=True)


    @app_commands.command(name="listcustoms", description="List all custom commands for this server")
    async def listcustoms(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        if guild_id in self.commands_per_guild and self.commands_per_guild[guild_id]:
            commands_list = "\n".join(f"/{name}: {response}" for name, response in self.commands_per_guild[guild_id].items())
            await interaction.response.send_message(f"Custom commands:\n{commands_list}", ephemeral=True)
        else:
            await interaction.response.send_message("No custom commands found for this server.", ephemeral=True)


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        guild_id = str(message.guild.id)
        if guild_id in self.commands_per_guild:
            cmd = message.content.lstrip("/").split(" ")[0].lower()
            if cmd in self.commands_per_guild[guild_id]:
                await message.channel.send(self.commands_per_guild[guild_id][cmd])

async def setup(bot):
    await bot.add_cog(CustomCommands(bot))