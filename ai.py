import discord
from discord.ext import commands
from discord import app_commands
import openai
import os
from dotenv import load_dotenv

load_dotenv()  # Add this line to load .env variables

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Get the key from .env
openai.api_key = OPENAI_API_KEY

class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ai", description="Chat with the AI (GPT-4o)")
    @app_commands.describe(prompt="What do you want to ask the AI?")
    async def ai(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7,
            )
            answer = response.choices[0].message.content
            await interaction.followup.send(answer)
        except Exception as e:
            await interaction.followup.send(f"Error: {e}")

async def setup(bot):
    await bot.add_cog(AI(bot))
