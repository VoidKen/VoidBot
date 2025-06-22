import os
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv(".env")
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("No token found. Please set the TOKEN environment variable.")

# Set up intents
intents = discord.Intents.all()
intents.message_content = True

bot = commands.Bot(command_prefix=".", intents=intents)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("That command does not exist.")
    else:
        await ctx.send(f"An error occurred: {error}")

@bot.command()
async def ping(ctx):
    """Check if the bot is responsive."""
    await ctx.send("Pong!")

@bot.event
async def on_message(message):
    await bot.process_commands(message)

async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"Loaded cog: {filename}")
            except Exception as e:
                print(f"Failed to load cog {filename}: {e}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        # This syncs all slash commands globally
        await bot.tree.sync()
        print("Slash commands synced globally.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

async def main():
    await load_cogs()
    await bot.start(TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())