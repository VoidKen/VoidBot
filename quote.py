import discord
from discord.ext import commands
from discord import app_commands
import json
import os

QUOTES_FILE = "quotes.json"

def load_quotes():
    if not os.path.exists(QUOTES_FILE):
        with open(QUOTES_FILE, "w") as f:
            json.dump({}, f)
    with open(QUOTES_FILE, "r") as f:
        return json.load(f)

def save_quotes(quotes):
    with open(QUOTES_FILE, "w") as f:
        json.dump(quotes, f, indent=2)

class Quotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.quotes = load_quotes()

    @app_commands.command(name="addquote", description="Save a quote")
    @app_commands.describe(quote="The quote text")
    async def addquote(self, interaction: discord.Interaction, quote: str):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.quotes:
            self.quotes[guild_id] = []
        self.quotes[guild_id].append({
            "quote": quote,
            "author": str(interaction.user),
            "author_id": interaction.user.id
        })
        save_quotes(self.quotes)
        await interaction.response.send_message(f"Quote saved! (#{len(self.quotes[guild_id])})", ephemeral=True)

    @app_commands.command(name="quote", description="Get a quote by number (or random if blank)")
    @app_commands.describe(number="Quote number (optional)")
    async def quote(self, interaction: discord.Interaction, number: int = None):
        guild_id = str(interaction.guild.id)
        quotes = self.quotes.get(guild_id, [])
        if not quotes:
            await interaction.response.send_message("No quotes saved yet.", ephemeral=True)
            return
        if number is None or number < 1 or number > len(quotes):
            import random
            quote = random.choice(quotes)
            idx = quotes.index(quote) + 1
        else:
            quote = quotes[number - 1]
            idx = number
        embed = discord.Embed(
            description=quote["quote"],
            color=discord.Color.purple()
        )
        embed.set_footer(text=f"Quote #{idx} — added by {quote['author']}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="listquotes", description="List all quotes for this server")
    async def listquotes(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        quotes = self.quotes.get(guild_id, [])
        if not quotes:
            await interaction.response.send_message("No quotes saved yet.", ephemeral=True)
            return
        msg = "\n".join([f"#{i+1}: {q['quote']} (by {q['author']})" for i, q in enumerate(quotes)])
        # Discord messages have a 2000 character limit
        if len(msg) > 1900:
            msg = msg[:1900] + "\n..."
        await interaction.response.send_message(f"**Quotes:**\n{msg}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Quotes(bot))