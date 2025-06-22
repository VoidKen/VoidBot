import discord
from discord.ext import commands
from discord import app_commands
import openai
import os

OPENAI_API_KEY = "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"  # Replace with your OpenAI API key
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
                model="gpt-4o",  # Use "gpt-4-1106-preview" for GPT-4.1 preview if available
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