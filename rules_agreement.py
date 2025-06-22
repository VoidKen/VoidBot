import discord
from discord.ext import commands
from discord import app_commands

RULES_FILE = "rules_settings.json"

import json
import os

def load_settings():
    if not os.path.exists(RULES_FILE):
        with open(RULES_FILE, "w") as f:
            json.dump({}, f)
    with open(RULES_FILE, "r") as f:
        return json.load(f)

def save_settings(settings):
    with open(RULES_FILE, "w") as f:
        json.dump(settings, f, indent=2)

class RulesAgreement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = load_settings()

    @app_commands.command(name="sendrules", description="Send the rules agreement embed")
    @app_commands.describe(channel="Channel to send the rules in", rules="The rules text", role="Role to give on agreement")
    @app_commands.checks.has_permissions(administrator=True)
    async def sendrules(self, interaction: discord.Interaction, channel: discord.TextChannel, rules: str, role: discord.Role):
        guild_id = str(interaction.guild.id)
        self.settings[guild_id] = {"role_id": role.id}
        save_settings(self.settings)

        embed = discord.Embed(
            title="Server Rules",
            description=rules,
            color=discord.Color.blue()
        )
        embed.set_footer(text="Click the button below to agree to the rules and get access!")

        view = RulesButton(role.id)
        await channel.send(embed=embed, view=view)
        await interaction.response.send_message("Rules embed sent!", ephemeral=True)

class RulesButton(discord.ui.View):
    def __init__(self, role_id):
        super().__init__(timeout=None)
        self.role_id = role_id

    @discord.ui.button(label="I Agree", style=discord.ButtonStyle.success, custom_id="agree_rules")
    async def agree(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(self.role_id)
        if role:
            await interaction.user.add_roles(role, reason="Agreed to rules")
            await interaction.response.send_message("You have agreed to the rules and have been given access!", ephemeral=True)
        else:
            await interaction.response.send_message("Role not found. Please contact an admin.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RulesAgreement(bot))