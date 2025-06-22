import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os
import json

DEEPL_API_KEY = "99018dd5-7c70-4100-bde6-a4fd3a73b61d:fx"  # Get from https://www.deepl.com/pro-api

TRANSLATE_FILE = "translate_settings.json"

def load_settings():
    if not os.path.exists(TRANSLATE_FILE):
        with open(TRANSLATE_FILE, "w") as f:
            json.dump({}, f)
    with open(TRANSLATE_FILE, "r") as f:
        return json.load(f)

def save_settings(settings):
    with open(TRANSLATE_FILE, "w") as f:
        json.dump(settings, f, indent=2)

class AutoTranslate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = load_settings()

    @app_commands.command(name="setautotranslate", description="Enable auto-translate in this channel")
    @app_commands.describe(target_lang="Target language code (e.g. EN, ES, FR, JA, etc.)")
    @app_commands.checks.has_permissions(administrator=True)
    async def setautotranslate(self, interaction: discord.Interaction, target_lang: str):
        channel_id = str(interaction.channel.id)
        self.settings[channel_id] = target_lang.upper()
        save_settings(self.settings)
        await interaction.response.send_message(f"Auto-translate enabled in this channel to `{target_lang.upper()}`.", ephemeral=True)

    @app_commands.command(name="disableautotranslate", description="Disable auto-translate in this channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def disableautotranslate(self, interaction: discord.Interaction):
        channel_id = str(interaction.channel.id)
        if channel_id in self.settings:
            del self.settings[channel_id]
            save_settings(self.settings)
            await interaction.response.send_message("Auto-translate disabled in this channel.", ephemeral=True)
        else:
            await interaction.response.send_message("Auto-translate is not enabled in this channel.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        channel_id = str(message.channel.id)
        target_lang = self.settings.get(channel_id)
        if not target_lang:
            return
        # Don't translate bot's own translations
        if message.webhook_id or message.author.bot:
            return
        # Translate the message
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api-free.deepl.com/v2/translate",
                data={
                    "auth_key": DEEPL_API_KEY,
                    "text": message.content,
                    "target_lang": target_lang
                }
            ) as resp:
                data = await resp.json()
                if "translations" in data:
                    translated = data["translations"][0]["text"]
                    await message.channel.send(
                        f"**Translated ({target_lang}):** {translated}",
                        reference=message
                    )

async def setup(bot):
    await bot.add_cog(AutoTranslate(bot))