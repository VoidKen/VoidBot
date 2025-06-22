import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
import datetime
from googletrans import Translator
from dateutil.relativedelta import relativedelta
import requests
import random
import os
import time



class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.birthdays = {}
        self.reminders = {}
        self.translator = Translator()
        self.start_time = time.time()  # Add this line

    @app_commands.command(name="botinfo", description="Show information about the bot")
    async def botinfo(self, interaction: discord.Interaction):
        uptime = time.time() - self.start_time
        hours, remainder = divmod(int(uptime), 3600)
        minutes, seconds = divmod(remainder, 60)
        embed = discord.Embed(title="Bot Information", color=discord.Color.green())
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)} ms")
        embed.add_field(name="Uptime", value=f"{hours}h {minutes}m {seconds}s")
        embed.set_footer(text="Made by VoidKen")
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="avatar", description="Get a user's avatar")
    @app_commands.describe(member="The member to get the avatar of")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        embed = discord.Embed(title=f"{member.display_name}'s Avatar")
        embed.set_image(url=member.avatar.url)
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="weather", description="Get the current weather for a location")
    @app_commands.describe(location="The location to get the weather for")
    async def weather(self, interaction: discord.Interaction, location: str):
        api_key = "YOUR_OPENWEATHERMAP_API_KEY"
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric") as response:
                if response.status == 200:
                    weather_data = await response.json()
                    weather_desc = weather_data['weather'][0]['description']
                    temp_celsius = weather_data['main']['temp']
                    temp_fahrenheit = (temp_celsius * 9/5) + 32
                    await interaction.response.send_message(f"The current weather in {location} is {weather_desc} with a temperature of {temp_celsius}°C ({temp_fahrenheit}°F).")
                else:
                    await interaction.response.send_message("Couldn't fetch the weather at the moment, try again later.")

    @app_commands.command(name="forecast", description="Get the weather forecast for a location")
    @app_commands.describe(location="The location to get the forecast for")
    async def forecast(self, interaction: discord.Interaction, location: str):
        api_key = "YOUR_OPENWEATHERMAP_API_KEY"
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://api.openweathermap.org/data/2.5/forecast?q={location}&appid={api_key}&units=metric") as response:
                if response.status == 200:
                    forecast_data = await response.json()
                    forecast_list = forecast_data['list'][:5]
                    forecast_message = "\n".join([f"{item['dt_txt']}: {item['weather'][0]['description']}, {item['main']['temp']}°C" for item in forecast_list])
                    await interaction.response.send_message(f"Weather forecast for {location}:\n{forecast_message}")
                else:
                    await interaction.response.send_message("Couldn't fetch the forecast at the moment, try again later.")

    @app_commands.command(name="news", description="Get the latest news")
    @app_commands.describe(category="The news category (e.g., business, entertainment, general, health, science, sports, technology)")
    async def news(self, interaction: discord.Interaction, category: str = "general"):
        api_key = "YOUR_NEWSAPI_KEY"
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://newsapi.org/v2/top-headlines?category={category}&apiKey={api_key}&country=us") as response:
                if response.status == 200:
                    news_data = await response.json()
                    articles = news_data.get('articles', [])
                    if articles:
                        top_article = articles[0]
                        title = top_article['title']
                        description = top_article['description']
                        url = top_article['url']
                        await interaction.response.send_message(f"**{title}**\n{description}\nRead more: {url}")
                    else:
                        await interaction.response.send_message("No news articles found for the specified category.")
                else:
                    await interaction.response.send_message("Couldn't fetch the news at the moment, try again later.")

    @app_commands.command(name="translate", description="Translate text to a specified language")
    @app_commands.describe(text="The text to translate", dest="The destination language (e.g., 'en' for English)")
    async def translate(self, interaction: discord.Interaction, text: str, dest: str):
        translation = self.translator.translate(text, dest=dest)
        await interaction.response.send_message(f"Translated text: {translation.text}")

    @app_commands.command(name="convert_currency", description="Convert currency from one type to another")
    @app_commands.describe(amount="The amount to convert", from_currency="The currency to convert from", to_currency="The currency to convert to")
    async def convert_currency(self, interaction: discord.Interaction, amount: float, from_currency: str, to_currency: str):
        response = requests.get(f"https://api.exchangerate-api.com/v4/latest/{from_currency}")
        if response.status_code == 200:
            rates = response.json().get("rates", {})
            rate = rates.get(to_currency)
            if rate:
                converted_amount = amount * rate
                await interaction.response.send_message(f"{amount} {from_currency} is equal to {converted_amount} {to_currency}")
            else:
                await interaction.response.send_message(f"Currency {to_currency} not found.")
        else:
            await interaction.response.send_message("Couldn't fetch currency rates at the moment, try again later.")


    @app_commands.command(name="set_birthday", description="Set your birthday")
    @app_commands.describe(date="Your birthday in YYYY-MM-DD format")
    async def set_birthday(self, interaction: discord.Interaction, date: str):
        try:
            datetime.datetime.strptime(date, "%Y-%m-%d")
            self.birthdays[interaction.user.id] = date
            await interaction.response.send_message(f"Birthday set to {date}")
        except ValueError:
            await interaction.response.send_message("Invalid date format. Please use YYYY-MM-DD.")

    @app_commands.command(name="get_birthday", description="Get a user's birthday")
    @app_commands.describe(member="The member to get the birthday of")
    async def get_birthday(self, interaction: discord.Interaction, member: discord.Member):
        date = self.birthdays.get(member.id)
        if date:
            await interaction.response.send_message(f"{member.mention}'s birthday is on {date}")
        else:
            await interaction.response.send_message(f"{member.mention} has not set a birthday.")

    @app_commands.command(name="list_reminders", description="List all your active reminders")
    async def list_reminders(self, interaction: discord.Interaction):
        user_reminders = self.reminders.get(interaction.user.id, [])
        if user_reminders:
            reminder_list = "\n".join([f"{i+1}. {reminder['message']} at {reminder['time']}" for i, reminder in enumerate(user_reminders)])
            await interaction.response.send_message(f"Your active reminders:\n{reminder_list}")
        else:
            await interaction.response.send_message("You have no active reminders.")

    @app_commands.command(name="delete_reminder", description="Delete a specific reminder")
    @app_commands.describe(reminder_index="The index of the reminder to delete")
    async def delete_reminder(self, interaction: discord.Interaction, reminder_index: int):
        user_reminders = self.reminders.get(interaction.user.id, [])
        if 0 < reminder_index <= len(user_reminders):
            removed_reminder = user_reminders.pop(reminder_index - 1)
            await interaction.response.send_message(f"Deleted reminder: {removed_reminder['message']} at {removed_reminder['time']}")
        else:
            await interaction.response.send_message("Invalid reminder index.")

    @app_commands.command(name="serverinfo", description="Get server information")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(title=guild.name, description="Server Information")
        embed.add_field(name="Server ID", value=guild.id)
        embed.add_field(name="Member Count", value=guild.member_count)
        embed.add_field(name="Owner", value=guild.owner)
        embed.add_field(name="Preferred Locale", value=guild.preferred_locale)
        embed.set_thumbnail(url=guild.icon.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Get user information")
    @app_commands.describe(member="The member to get information about")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member):
        embed = discord.Embed(title=member.name, description="User Information")
        embed.add_field(name="User ID", value=member.id)
        embed.add_field(name="Joined Server", value=member.joined_at)
        embed.add_field(name="Account Created", value=member.created_at)
        embed.set_thumbnail(url=member.avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="roleinfo", description="Get role information")
    @app_commands.describe(role="The role to get information about")
    async def roleinfo(self, interaction: discord.Interaction, role: discord.Role):
        embed = discord.Embed(title=role.name, description="Role Information")
        embed.add_field(name="Role ID", value=role.id)
        embed.add_field(name="Color", value=str(role.color))
        embed.add_field(name="Created At", value=role.created_at)
        embed.add_field(name="Permissions", value=", ".join([perm[0] for perm in role.permissions if perm[1]]))
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="server_stats", description="Get detailed server statistics")
    async def server_stats(self, interaction: discord.Interaction):
        guild = interaction.guild
        total_members = guild.member_count
        online_members = sum(1 for member in guild.members if member.status != discord.Status.offline)
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        roles = len(guild.roles)

        embed = discord.Embed(title="Server Statistics", description=f"Statistics for {guild.name}")
        embed.add_field(name="Total Members", value=total_members)
        embed.add_field(name="Online Members", value=online_members)
        embed.add_field(name="Text Channels", value=text_channels)
        embed.add_field(name="Voice Channels", value=voice_channels)
        embed.add_field(name="Roles", value=roles)
        embed.set_thumbnail(url=guild.icon.url)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="help", description="Show all commands, grouped by category")
    async def help_command(self, interaction: discord.Interaction):
        bot = self.bot
        cogs = {}
        is_admin = interaction.user.guild_permissions.administrator

        for cmd in bot.tree.get_commands(guild=interaction.guild):
            # Check if admin perms are required
            admin_required = False
            for check in getattr(cmd, "checks", []):
                if hasattr(check, "__qualname__") and "has_permissions" in check.__qualname__:
                    admin_required = True

            # Filter out admin commands for non-admins
            if admin_required and not is_admin:
                continue

            cog_name = cmd.module.split('.')[-1].capitalize() if cmd.module else "Other"
            if cog_name not in cogs:
                cogs[cog_name] = []
            params = [f"<{opt.name}>" for opt in getattr(cmd, "options", [])]
            param_str = " " + " ".join(params) if params else ""
            admin_tag = " [Admin]" if admin_required else ""
            cogs[cog_name].append(f"/{cmd.name}{param_str}: {cmd.description}{admin_tag}")

        embed = discord.Embed(title="Help", description="All available commands, grouped by category.", color=discord.Color.blue())
        for cog, commands in sorted(cogs.items()):
            if not commands:
                continue
            value = ""
            for cmd in commands:
                if len(value) + len(cmd) + 1 > 1024:
                    embed.add_field(name=f"{cog} Commands", value=value, inline=False)
                    value = ""
                value += cmd + "\n"
            if value:
                embed.add_field(name=f"{cog} Commands", value=value, inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))