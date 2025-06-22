import discord
from discord.ext import commands

BANNED_WORDS = ["badword1", "badword2", "anotherbadword"]  # Add your banned words here
BANNED_LINKS = ["discord.gg/", "bit.ly/", "spamlink.com"]  # Add banned links or domains

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None or message.author.bot:
            return

        # Check for banned words
        for word in BANNED_WORDS:
            if word in message.content.lower():
                await message.delete()
                await message.channel.send(f"{message.author.mention}, that word is not allowed here!", delete_after=5)
                return

        # Check for banned links
        for link in BANNED_LINKS:
            if link in message.content.lower():
                await message.delete()
                await message.channel.send(f"{message.author.mention}, links like that are not allowed!", delete_after=5)
                return

async def setup(bot):
    await bot.add_cog(AutoMod(bot))