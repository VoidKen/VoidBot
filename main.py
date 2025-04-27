import datetime
import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
from dotenv import load_dotenv
import random
import asyncio
import aiohttp
from googletrans import Translator
from dateutil.relativedelta import relativedelta
import requests
import json
import yt_dlp as youtube_dl  # Change this line
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
load_dotenv(".env")
TOKEN = os.getenv("TOKEN")
GUILD_ID = 1088586791516393622  # Update this to your new guild ID

class Client(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.song_queue = []  # Renamed from self.queue
        self.currently_playing = None
        self.voice_client = None
        self.ping_task = self.create_ping_task()

    def create_ping_task(self):
        @tasks.loop(seconds=60)
        async def ping_task():
            await self.wait_until_ready()
            while not self.is_closed():
                # Replace with your desired ping logic
                print("Pinging...")
                await asyncio.sleep(60)  # Ping every 60 seconds
        return ping_task

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Command not found.")

    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        
        try:
            guild = discord.Object(id=GUILD_ID)
            synced = await self.tree.sync(guild=guild)
            print(f'Synced {len(synced)} commands to guild {guild.id}')
        except Exception as e:
            print(f'Error syncing commands: {e}')
        
        self.ping_task.start()  # Start the task here

intents = discord.Intents.all()
intents.message_content = True
bot = Client(command_prefix=".", intents=intents)

# Update ytdl_format_options and ffmpeg_options if necessary
ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename
@bot.tree.command(name='join', description='Tells the bot to join the voice channel', guild=discord.Object(id=GUILD_ID))
async def join(interaction: discord.Interaction):
    if not interaction.user.voice:
        await interaction.response.send_message(f"{interaction.user.name} is not connected to a voice channel")
        return
    else:
        channel = interaction.user.voice.channel
    await channel.connect()
    await interaction.response.send_message(f"Joined {channel.name}")

@bot.tree.command(name='leave', description='To make the bot leave the voice channel', guild=discord.Object(id=GUILD_ID))
async def leave(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
        await interaction.response.send_message("Left the voice channel")
    else:
        await interaction.response.send_message("The bot is not connected to a voice channel.")

@bot.tree.command(name='play_song', description='To play song', guild=discord.Object(id=GUILD_ID))
@app_commands.describe(url="The URL of the song to play")
async def play(interaction: discord.Interaction, url: str):
    server = interaction.guild
    voice_channel = server.voice_client

    if not voice_channel:
        if interaction.user.voice:
            channel = interaction.user.voice.channel
            await channel.connect()
            voice_channel = server.voice_client
        else:
            await interaction.response.send_message("You need to be in a voice channel to play music.")
            return

    bot.song_queue.append(url)
    await interaction.response.send_message(f"Added to queue: {url}")

    if not voice_channel.is_playing():
        await play_next_song(voice_channel)

async def play_next_song(voice_channel):
    if bot.song_queue:
        next_song = bot.song_queue.pop(0)
        filename = await YTDLSource.from_url(next_song, loop=bot.loop)
        voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename), after=lambda e: bot.loop.create_task(play_next_song(voice_channel)))
        await voice_channel.guild.system_channel.send(f'**Now playing:** {filename}')
    else:
        await voice_channel.guild.system_channel.send("The queue is empty.")

@bot.tree.command(name='pause', description='This command pauses the song', guild=discord.Object(id=GUILD_ID))
async def pause(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client.is_playing():
        await voice_client.pause()
        await interaction.response.send_message("Paused the song")
    else:
        await interaction.response.send_message("The bot is not playing anything at the moment.")

@bot.tree.command(name='resume', description='Resumes the song', guild=discord.Object(id=GUILD_ID))
async def resume(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client.is_paused():
        await voice_client.resume()
        await interaction.response.send_message("Resumed the song")
    else:
        await interaction.response.send_message("The bot was not playing anything before this. Use play_song command")

@bot.tree.command(name='stop', description='Stops the song', guild=discord.Object(id=GUILD_ID))
async def stop(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client.is_playing():
        voice_client.stop()
        bot.song_queue.clear()
        await interaction.response.send_message("Stopped the song and cleared the queue")
    else:
        await interaction.response.send_message("The bot is not playing anything at the moment.")
# Add to Queue
@bot.tree.command(name='add_to_queue', description='Add a song to the queue', guild=discord.Object(id=GUILD_ID))
@app_commands.describe(url="The URL of the song to add")
async def add_to_queue(interaction: discord.Interaction, url: str):
    bot.song_queue.append(url)
    await interaction.response.send_message(f"Added {url} to the queue")

# View Queue
@bot.tree.command(name='view_queue', description='View the current song queue', guild=discord.Object(id=GUILD_ID))
async def view_queue(interaction: discord.Interaction):
    if bot.song_queue:
        queue_list = "\n".join([f"{i+1}. {url}" for i, url in enumerate(bot.song_queue)])
        await interaction.response.send_message(f"Current queue:\n{queue_list}")
    else:
        await interaction.response.send_message("The queue is empty")

# Skip
@bot.tree.command(name='skip', description='Skip the currently playing song', guild=discord.Object(id=GUILD_ID))
async def skip(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client.is_playing():
        voice_client.stop()
        await interaction.response.send_message("Skipped the song")
        await play_next_song(voice_client)
    else:
        await interaction.response.send_message("The bot is not playing anything at the moment")
# Clear Queue
@bot.tree.command(name='clear_queue', description='Clear the song queue', guild=discord.Object(id=GUILD_ID))
async def clear_queue(interaction: discord.Interaction):
    bot.song_queue.clear()
@bot.tree.command(name='volume', description='Change the volume of the music', guild=discord.Object(id=GUILD_ID))
@app_commands.describe(volume="The volume level (0-100)")
async def volume(interaction: discord.Interaction, volume: int):
    voice_client = interaction.guild.voice_client
    if voice_client.is_playing():
        if 0 <= volume <= 100:
            voice_client.source.volume = volume / 100
            await interaction.response.send_message(f"Volume set to {volume}%")
        else:
            await interaction.response.send_message("Volume must be between 0 and 100")
    else:
        await interaction.response.send_message("The bot is not playing anything at the moment.")
# Load levels from file
def load_levels():
    if os.path.exists("levels.json"):
        with open("levels.json", "r") as f:
            return json.load(f)
    return {}

# Save levels to file
def save_levels():
    with open("levels.json", "w") as f:
        json.dump(levels, f)

levels = load_levels()

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    if user_id not in levels:
        levels[user_id] = {"xp": 0, "level": 1}

    levels[user_id]["xp"] += 10
    if levels[user_id]["xp"] >= levels[user_id]["level"] * 100:
        levels[user_id]["xp"] = 0
        levels[user_id]["level"] += 1
        await message.channel.send(f"Congratulations {message.author.mention}, you leveled up to level {levels[user_id]['level']}!")

    save_levels()
    await bot.process_commands(message)

@bot.tree.command(name="level", description="Check your level", guild=discord.Object(id=GUILD_ID))
async def level(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if user_id in levels:
        level = levels[user_id]["level"]
        xp = levels[user_id]["xp"]
        await interaction.response.send_message(f"You are level {level} with {xp} XP.")
    else:
        await interaction.response.send_message("You have no levels yet.")

@bot.tree.command(name="leaderboard", description="Show the top users by level", guild=discord.Object(id=GUILD_ID))
async def leaderboard(interaction: discord.Interaction):
    sorted_levels = sorted(levels.items(), key=lambda x: x[1]["level"], reverse=True)
    leaderboard_message = "\n".join([f"{i+1}. <@{user_id}> - Level {data['level']}" for i, (user_id, data) in enumerate(sorted_levels[:10])])
    await interaction.response.send_message(f"**Leaderboard**\n{leaderboard_message}")

@bot.tree.command(name="set_xp", description="Set the XP for a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(member="The member to set XP for", xp="The amount of XP to set")
@commands.has_permissions(administrator=True)
async def set_xp(interaction: discord.Interaction, member: discord.Member, xp: int):
    user_id = str(member.id)
    if user_id in levels:
        levels[user_id]["xp"] = xp
        save_levels()
        await interaction.response.send_message(f"Set {member.mention}'s XP to {xp}.")
    else:
        await interaction.response.send_message(f"{member.mention} has no levels yet.")

@bot.tree.command(name="set_level", description="Set the level for a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(member="The member to set level for", level="The level to set")
@commands.has_permissions(administrator=True)
async def set_level(interaction: discord.Interaction, member: discord.Member, level: int):
    user_id = str(member.id)
    if user_id in levels:
        levels[user_id]["level"] = level
        save_levels()
        await interaction.response.send_message(f"Set {member.mention}'s level to {level}.")
    else:
        await interaction.response.send_message(f"{member.mention} has no levels yet.")

@bot.tree.command(name="user_stats", description="Get detailed user statistics", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(member="The member to get statistics for")
async def user_stats(interaction: discord.Interaction, member: discord.Member):
    user_id = str(member.id)
    if user_id in levels:
        level = levels[user_id]["level"]
        xp = levels[user_id]["xp"]
        await interaction.response.send_message(f"{member.mention} is level {level} with {xp} XP.")
    else:
        await interaction.response.send_message(f"{member.mention} has no levels yet.")

@bot.tree.command(name="hello", description="Say Hello!", guild=discord.Object(id=GUILD_ID))
async def sayHello(interaction: discord.Interaction):
    await interaction.response.send_message("Hi There!")

@bot.tree.command(name="ping", description="Get the bot's latency", guild=discord.Object(id=GUILD_ID))
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! {round(bot.latency * 1000)}ms")

@bot.tree.command(name="say", description="Make the bot say something", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(message="The message to say")
async def say(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(message)

@bot.tree.command(name="convert_currency", description="Convert currency from one type to another", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(amount="The amount to convert", from_currency="The currency to convert from", to_currency="The currency to convert to")
async def convert_currency(interaction: discord.Interaction, amount: float, from_currency: str, to_currency: str):
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
@bot.tree.command(name="remind", description="Set a reminder", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(time="Time in seconds", message="Reminder message")
async def remind(interaction: discord.Interaction, time: int, message: str):
    await interaction.response.send_message(f"Reminder set for {time} seconds.")
    await asyncio.sleep(time)
    await interaction.followup.send(f"Reminder: {message}")
birthdays = {}

@bot.tree.command(name="set_birthday", description="Set your birthday", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(date="Your birthday in YYYY-MM-DD format")
async def set_birthday(interaction: discord.Interaction, date: str):
    try:
        datetime.datetime.strptime(date, "%Y-%m-%d")
        birthdays[interaction.user.id] = date
        await interaction.response.send_message(f"Birthday set to {date}")
    except ValueError:
        await interaction.response.send_message("Invalid date format. Please use YYYY-MM-DD.")
translator = Translator()

@bot.tree.command(name="translate", description="Translate text to a specified language", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(text="The text to translate", dest="The destination language (e.g., 'en' for English)")
async def translate(interaction: discord.Interaction, text: str, dest: str):
    translation = translator.translate(text, dest=dest)
    await interaction.response.send_message(f"Translated text: {translation.text}")
@bot.tree.command(name="get_birthday", description="Get a user's birthday", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(member="The member to get the birthday of")
async def get_birthday(interaction: discord.Interaction, member: discord.Member):
    date = birthdays.get(member.id)
    if date:
        await interaction.response.send_message(f"{member.mention}'s birthday is on {date}")
    else:
        await interaction.response.send_message(f"{member.mention} has not set a birthday.")

@bot.tree.command(name="remind_at", description="Set a reminder at a specific date and time", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(datetime="The date and time for the reminder in YYYY-MM-DD HH:MM format", message="Reminder message")
async def remind_at(interaction: discord.Interaction, datetime: str, message: str):
    try:
        reminder_time = datetime.datetime.strptime(datetime, "%Y-%m-%d %H:%M")
        now = datetime.datetime.now()
        delay = (reminder_time - now).total_seconds()
        if delay > 0:
            await interaction.response.send_message(f"Reminder set for {datetime}.")
            await asyncio.sleep(delay)
            await interaction.followup.send(f"Reminder: {message}")
        else:
            await interaction.response.send_message("The specified time is in the past.")
    except ValueError:
        await interaction.response.send_message("Invalid date and time format. Please use YYYY-MM-DD HH:MM.")

@bot.tree.command(name="remind_every", description="Set a recurring reminder", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(interval="The interval in seconds", message="Reminder message")
async def remind_every(interaction: discord.Interaction, interval: int, message: str):
    await interaction.response.send_message(f"Recurring reminder set for every {interval} seconds.")
    while True:
        await asyncio.sleep(interval)
        await interaction.followup.send(f"Reminder: {message}")
@bot.tree.command(name="remind_daily", description="Set a daily reminder", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(time="The time of the reminder in HH:MM format", message="Reminder message")
async def remind_daily(interaction: discord.Interaction, time: str, message: str):
    try:
        reminder_time = datetime.datetime.strptime(time, "%H:%M")
        now = datetime.datetime.now()
        reminder_time = reminder_time.replace(year=now.year, month=now.month, day=now.day)
        if reminder_time < now:
            reminder_time += datetime.timedelta(days=1)
        delay = (reminder_time - now).total_seconds()
        await interaction.response.send_message(f"Daily reminder set for {time}.")
        while True:
            await asyncio.sleep(delay)
            await interaction.followup.send(f"Reminder: {message}")
            delay = 86400  # 24 hours in seconds
    except ValueError:
        await interaction.response.send_message("Invalid time format. Please use HH:MM.")
@bot.tree.command(name="remind_weekly", description="Set a weekly reminder", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(day="The day of the week for the reminder (e.g., Monday, Tuesday, etc.)", time="The time of the reminder in HH:MM format", message="Reminder message")
async def remind_weekly(interaction: discord.Interaction, day: str, time: str, message: str):
    try:
        reminder_time = datetime.datetime.strptime(time, "%H:%M")
        now = datetime.datetime.now()
        reminder_time = reminder_time.replace(year=now.year, month=now.month, day=now.day)
        reminder_time += datetime.timedelta(days=(7 - reminder_time.weekday() + ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(day)) % 7)
        if reminder_time < now:
            reminder_time += datetime.timedelta(weeks=1)
        delay = (reminder_time - now).total_seconds()
        await interaction.response.send_message(f"Weekly reminder set for {day} at {time}.")
        while True:
            await asyncio.sleep(delay)
            await interaction.followup.send(f"Reminder: {message}")
            delay = 604800  # 7 days in seconds
    except ValueError:
        await interaction.response.send_message("Invalid time format. Please use HH:MM.")
@bot.tree.command(name="remind_monthly", description="Set a monthly reminder", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(day="The day of the month for the reminder", time="The time of the reminder in HH:MM format", message="Reminder message")
async def remind_monthly(interaction: discord.Interaction, day: int, time: str, message: str):
    try:
        reminder_time = datetime.datetime.strptime(time, "%H:%M")
        now = datetime.datetime.now()
        reminder_time = reminder_time.replace(year=now.year, month=now.month, day=day)
        if reminder_time < now:
            reminder_time += relativedelta(months=1)
        delay = (reminder_time - now).total_seconds()
        await interaction.response.send_message(f"Monthly reminder set for {day} at {time}.")
        while True:
            await asyncio.sleep(delay)
            await interaction.followup.send(f"Reminder: {message}")
            delay = 2592000  # 30 days in seconds
    except ValueError:
        await interaction.response.send_message("Invalid time format. Please use HH:MM.")
@bot.tree.command(name="remind_yearly", description="Set a yearly reminder", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(date="The date of the reminder in MM-DD format", time="The time of the reminder in HH:MM format", message="Reminder message")
async def remind_yearly(interaction: discord.Interaction, date: str, time: str, message: str):
    try:
        reminder_time = datetime.datetime.strptime(time, "%H:%M")
        now = datetime.datetime.now()
        reminder_time = reminder_time.replace(year=now.year, month=int(date.split("-")[0]), day=int(date.split("-")[1]))
        if reminder_time < now:
            reminder_time += relativedelta(years=1)
        delay = (reminder_time - now).total_seconds()
        await interaction.response.send_message(f"Yearly reminder set for {date} at {time}.")
        while True:
            await asyncio.sleep(delay)
            await interaction.followup.send(f"Reminder: {message}")
            delay = 31536000  # 365 days in seconds
    except ValueError:
        await interaction.response.send_message("Invalid date or time format. Please use MM-DD and HH:MM.")
@bot.tree.command(name="remind_custom", description="Set a custom reminder", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(datetime="The date and time for the reminder in YYYY-MM-DD HH:MM format", message="Reminder message")
async def remind_custom(interaction: discord.Interaction, datetime: str, message: str):
    try:
        reminder_time = datetime.datetime.strptime(datetime, "%Y-%m-%d %H:%M")
        now = datetime.datetime.now()
        delay = (reminder_time - now).total_seconds()
        if delay > 0:
            await interaction.response.send_message(f"Custom reminder set for {datetime}.")
            await asyncio.sleep(delay)
            await interaction.followup.send(f"Reminder: {message}")
        else:
            await interaction.response.send_message("The specified time is in the past.")
    except ValueError:
        await interaction.response.send_message("Invalid date and time format. Please use YYYY-MM-DD HH:MM.")
user_statistics = {}
  
@bot.tree.command(name="trivia", description="Start a trivia game", guild=discord.Object(id=GUILD_ID))
async def trivia(interaction: discord.Interaction):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://opentdb.com/api.php?amount=1&type=multiple") as response:
            if response.status == 200:
                trivia_data = await response.json()
                question_data = trivia_data['results'][0]
                question = question_data['question']
                correct_answer = question_data['correct_answer']
                incorrect_answers = question_data['incorrect_answers']
                options = incorrect_answers + [correct_answer]
                random.shuffle(options)

                def check(m):
                    return m.author == interaction.user and m.content in options

                await interaction.response.send_message(f"**Trivia Question:** {question}\nOptions: {', '.join(options)}")

                try:
                    msg = await bot.wait_for('message', check=check, timeout=30.0)
                except asyncio.TimeoutError:
                    await interaction.followup.send(f"Time's up! The correct answer was: {correct_answer}")
                else:
                    if msg.content == correct_answer:
                        await interaction.followup.send("Correct! 🎉")
                    else:
                        await interaction.followup.send(f"Wrong! The correct answer was: {correct_answer}")
            else:
                await interaction.response.send_message("Couldn't fetch a trivia question at the moment, try again later.")
@bot.tree.command(name="meme", description="Get a random meme", guild=discord.Object(id=GUILD_ID))
async def meme(interaction: discord.Interaction):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://www.reddit.com/r/memes/random/.json") as response:
            if response.status == 200:
                meme_data = await response.json()
                meme_url = meme_data[0]['data']['children'][0]['data']['url']
                await interaction.response.send_message(meme_url)
            else:
                await interaction.response.send_message("Couldn't fetch a meme at the moment, try again later.")
@bot.tree.command(name="cat", description="Get a random cat image", guild=discord.Object(id=GUILD_ID))
async def cat(interaction: discord.Interaction):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.thecatapi.com/v1/images/search") as response:
            if response.status == 200:
                cat_data = await response.json()
                cat_url = cat_data[0]['url']
                await interaction.response.send_message(cat_url)
            else:
                await interaction.response.send_message("Couldn't fetch a cat image at the moment, try again later.")
@bot.tree.command(name="dad_joke", description="Tell a random dad joke", guild=discord.Object(id=GUILD_ID))
async def dad_joke(interaction: discord.Interaction):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://icanhazdadjoke.com/", headers={"Accept": "application/json"}) as response:
            if response.status == 200:
                joke_data = await response.json()
                joke = joke_data['joke']
                await interaction.response.send_message(joke)
            else:
                await interaction.response.send_message("Couldn't fetch a joke at the moment, try again later.")                
@bot.tree.command(name="dog", description="Get a random dog image", guild=discord.Object(id=GUILD_ID))
async def dog(interaction: discord.Interaction):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.thedogapi.com/v1/images/search") as response:
            if response.status == 200:
                dog_data = await response.json()
                dog_url = dog_data[0]['url']
                await interaction.response.send_message(dog_url)
            else:
                await interaction.response.send_message("Couldn't fetch a dog image at the moment, try again later.")
@bot.tree.command(name="joke", description="Tell a random joke", guild=discord.Object(id=GUILD_ID))
async def joke(interaction: discord.Interaction):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://official-joke-api.appspot.com/random_joke") as response:
            if response.status == 200:
                joke_data = await response.json()
                joke = f"{joke_data['setup']} - {joke_data['punchline']}"
                await interaction.response.send_message(joke)
            else:
                await interaction.response.send_message("Couldn't fetch a joke at the moment, try again later.")
@bot.tree.command(name="quote", description="Get a random quote", guild=discord.Object(id=GUILD_ID))
async def quote(interaction: discord.Interaction):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.quotable.io/random") as response:
            if response.status == 200:
                quote_data = await response.json()
                quote = f"\"{quote_data['content']}\" - {quote_data['author']}"
                await interaction.response.send_message(quote)
            else:
                await interaction.response.send_message("Couldn't fetch a quote at the moment, try again later.")
@bot.tree.command(name="weather", description="Get the current weather for a location", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(location="The location to get the weather for")
async def weather(interaction: discord.Interaction, location: str):
    api_key = "81c1cce9ef4912f0c409e0fab2426dd5"
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
                await interaction.response.send_message("Couldn't fetch the weather at the moment, try again later.")
@bot.tree.command(name="news", description="Get the latest news", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(category="The news category (e.g., business, entertainment, general, health, science, sports, technology)")
async def news(interaction: discord.Interaction, category: str = "general"):
    api_key = "6d0d588bf8cf4716bb4fcef5e6562281"
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
@bot.tree.command(name="8ball", description="Ask the magic 8ball a question", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(question="The question to ask the 8ball")
async def eight_ball(interaction: discord.Interaction, question: str):
    responses = [
        "It is certain.",
        "It is decidedly so.",
        "Without a doubt.",
        "Yes – definitely.",
        "You may rely on it.",
        "As I see it, yes.",
        "Most likely.",
        "Outlook good.",
        "Yes.",
        "Signs point to yes.",
        "Reply hazy, try again.",
        "Ask again later.",
        "Better not tell you now.",
        "Cannot predict now.",
        "Concentrate and ask again.",
        "Don't count on it.",
        "My reply is no.",
        "My sources say no.",
        "Outlook not so good.",
        "Very doubtful."
    ]
    response = random.choice(responses)
    await interaction.response.send_message(f"🎱 {response}")
@bot.tree.command(name="serverinfo", description="Get server information", guild=discord.Object(id=GUILD_ID))
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(title=guild.name, description="Server Information")
    embed.add_field(name="Server ID", value=guild.id)
    embed.add_field(name="Member Count", value=guild.member_count)
    embed.add_field(name="Owner", value=guild.owner)
    embed.add_field(name="Preferred Locale", value=guild.preferred_locale)
    embed.set_thumbnail(url=guild.icon.url)
    await interaction.response.send_message(embed=embed)
@bot.tree.command(name="userinfo", description="Get user information", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(member="The member to get information about")
async def userinfo(interaction: discord.Interaction, member: discord.Member):
    embed = discord.Embed(title=member.name, description="User Information")
    embed.add_field(name="User ID", value=member.id)
    embed.add_field(name="Joined Server", value=member.joined_at)
    embed.add_field(name="Account Created", value=member.created_at)
    embed.set_thumbnail(url=member.avatar.url)
    await interaction.response.send_message(embed=embed)
@bot.tree.command(name="roleinfo", description="Get role information", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(role="The role to get information about")
async def roleinfo(interaction: discord.Interaction, role: discord.Role):
    embed = discord.Embed(title=role.name, description="Role Information")
    embed.add_field(name="Role ID", value=role.id)
    embed.add_field(name="Color", value=str(role.color))
    embed.add_field(name="Created At", value=role.created_at)
    embed.add_field(name="Permissions", value=", ".join([perm[0] for perm in role.permissions if perm[1]]))
    await interaction.response.send_message(embed=embed)
@bot.tree.command(name="forecast", description="Get the weather forecast for a location", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(location="The location to get the forecast for")
async def forecast(interaction: discord.Interaction, location: str):
    api_key = "81c1cce9ef4912f0c409e0fab2426dd5"
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://api.openweathermap.org/data/2.5/forecast?q={location}&appid={api_key}&units=metric") as response:
            if response.status == 200:
                forecast_data = await response.json()
                forecast_list = forecast_data['list'][:5]  # Get the forecast for the next 5 intervals
                forecast_message = "\n".join([f"{item['dt_txt']}: {item['weather'][0]['description']}, {item['main']['temp']}°C" for item in forecast_list])
                await interaction.response.send_message(f"Weather forecast for {location}:\n{forecast_message}")
            else:
                await interaction.response.send_message("Couldn't fetch the forecast at the moment, try again later.")

reminders = {}

@bot.tree.command(name="list_reminders", description="List all your active reminders", guild=discord.Object(id=GUILD_ID))
async def list_reminders(interaction: discord.Interaction):
    user_reminders = reminders.get(interaction.user.id, [])
    if user_reminders:
        reminder_list = "\n".join([f"{i+1}. {reminder['message']} at {reminder['time']}" for i, reminder in enumerate(user_reminders)])
        await interaction.response.send_message(f"Your active reminders:\n{reminder_list}")
    else:
        await interaction.response.send_message("You have no active reminders.")

@bot.tree.command(name="roll", description="Roll a dice", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(sides="The number of sides on the dice")
async def roll(interaction: discord.Interaction, sides: int = 6):
    result = random.randint(1, sides)
    await interaction.response.send_message(f"🎲 You rolled a {result} on a {sides}-sided dice")

@bot.tree.command(name="flip", description="Flip a coin", guild=discord.Object(id=GUILD_ID))
async def flip(interaction: discord.Interaction):
    result = random.choice(["Heads", "Tails"])
    await interaction.response.send_message(f"🪙 The coin landed on {result}")

@bot.tree.command(name="server_stats", description="Get detailed server statistics", guild=discord.Object(id=GUILD_ID))
async def server_stats(interaction: discord.Interaction):
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

@bot.tree.command(name="delete_reminder", description="Delete a specific reminder", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(reminder_index="The index of the reminder to delete")
async def delete_reminder(interaction: discord.Interaction, reminder_index: int):
    user_reminders = reminders.get(interaction.user.id, [])
    if 0 < reminder_index <= len(user_reminders):
        removed_reminder = user_reminders.pop(reminder_index - 1)
        await interaction.response.send_message(f"Deleted reminder: {removed_reminder['message']} at {removed_reminder['time']}")
    else:
        await interaction.response.send_message("Invalid reminder index.")
# Commands requiring admin permissions

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have the required permissions to use this command.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found.")
    else:
        raise error

@bot.tree.command(name="mute", description="Mute a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(member="The member to mute", reason="The reason for muting")
@commands.has_permissions(administrator=True)
async def mute(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    muted_role = discord.utils.get(interaction.guild.roles, name="Muted")
    if not muted_role:
        await interaction.response.send_message("Muted role not found. Please create a 'Muted' role.")
    await member.add_roles(muted_role, reason=reason)
    return
    await member.add_roles(muted_role, reason=reason)
    await interaction.response.send_message(f"Muted {member.mention} for: {reason}")

@bot.tree.command(name="poll", description="Create a poll", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(question="The poll question", options="Comma-separated list of options")
@commands.has_permissions(administrator=True)
async def poll(interaction: discord.Interaction, question: str, options: str):
    options_list = options.split(',')
    if len(options_list) < 2:
        await interaction.response.send_message("Please provide at least two options.")
        return

    embed = discord.Embed(title=question, description="\n".join([f"{i+1}. {option.strip()}" for i, option in enumerate(options_list)]))
    await interaction.response.send_message(embed=embed)
    message = await interaction.original_response()  # Get the original message object
    for i in range(len(options_list)):
        await message.add_reaction(chr(127462 + i))  # Adds reactions 🇦, 🇧, 🇨, etc.

@bot.tree.command(name="unmute", description="Unmute a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(member="The member to unmute")
@commands.has_permissions(administrator=True)
async def unmute(interaction: discord.Interaction, member: discord.Member):
    muted_role = discord.utils.get(interaction.guild.roles, name="Muted")
    if not muted_role:
        await interaction.response.send_message("Muted role not found. Please create a 'Muted' role.")
        return

    await member.remove_roles(muted_role)
    await interaction.response.send_message(f"Unmuted {member.mention}")

@bot.tree.command(name="kick", description="Kick a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(member="The member to kick", reason="The reason for kicking")
@commands.has_permissions(administrator=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    await member.kick(reason=reason)
    await interaction.response.send_message(f"Kicked {member.mention} for: {reason}")

@bot.tree.command(name="ban", description="Ban a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(member="The member to ban", reason="The reason for banning")
@commands.has_permissions(administrator=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    await member.ban(reason=reason)
    await interaction.response.send_message(f"Banned {member.mention} for: {reason}")

@bot.tree.command(name="unban", description="Unban a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(member="The member to unban")
@commands.has_permissions(administrator=True)
async def unban(interaction: discord.Interaction, member: discord.User):
    await interaction.guild.unban(member)
    await interaction.response.send_message(f"Unbanned {member.mention}")

@bot.tree.command(name="purge", description="Purge messages", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(amount="The amount of messages to purge")
@commands.has_permissions(administrator=True)
async def purge(interaction: discord.Interaction, amount: int):
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"Purged {amount} messages")
@bot.tree.command(name="giveaway", description="Host a giveaway", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(prize="The prize for the giveaway", duration="The duration of the giveaway in seconds")
@commands.has_permissions(administrator=True)
async def giveaway(interaction: discord.Interaction, prize: str, duration: int):
    embed = discord.Embed(title="Giveaway!", description=f"Prize: {prize}\nReact with 🎉 to enter!\nDuration: {duration} seconds")
    message = await interaction.response.send_message(embed=embed)
    await message.add_reaction("🎉")

    await asyncio.sleep(duration)

    message = await interaction.channel.fetch_message(message.id)
    users = await message.reactions[0].users().flatten()
    users.remove(bot.user)

    if users:
        winner = random.choice(users)
@bot.tree.command(name="sync", description="Sync the bot's commands", guild=discord.Object(id=GUILD_ID))
@commands.has_permissions(administrator=True)
async def sync(interaction: discord.Interaction):
    try:
        guild = discord.Object(id=GUILD_ID)
        synced = await bot.tree.sync(guild=guild)
        await interaction.response.send_message(f"Synced {len(synced)} commands to guild {guild.id}")
    except Exception as e:
        await interaction.response.send_message(f"Error syncing commands: {e}")
@bot.tree.command(name="start_pinging", description="Start pinging with custom intervals and message", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(channel_id="The channel ID to send pings to", member="The member to ping", hours="Hours interval", minutes="Minutes interval", seconds="Seconds interval", message="The custom message")
@commands.has_permissions(administrator=True)
async def start_pinging(interaction: discord.Interaction, channel_id: str, member: discord.Member, hours: int = 0, minutes: int = 0, seconds: int = 0, message: str = "Custom message!"):
    try:
        channel_id = int(channel_id)
    except ValueError:
        await interaction.response.send_message("Please provide a valid integer for the channel ID.")
        return

    if bot.ping_task is not None:
        bot.ping_task.cancel()
    
    @tasks.loop(hours=hours, minutes=minutes, seconds=seconds)
    async def ping_task():
        await bot.wait_until_ready()
        channel = bot.get_channel(channel_id)
        if channel:
            await bot.send_random_ping(channel, member, message)
    
    bot.ping_task = ping_task
    bot.ping_task.start()
    await interaction.response.send_message(f"Started pinging {member.mention} in channel {channel_id} with message: {message}")

@bot.tree.command(name="reaction_role", description="Set up a reaction role", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(message_id="The ID of the message to add reactions to", emoji="The emoji to react with", role="The role to assign")
@commands.has_permissions(administrator=True)
async def reaction_role(interaction: discord.Interaction, message_id: int, emoji: str, role: discord.Role):
    message = await interaction.channel.fetch_message(message_id)
    await message.add_reaction(emoji)

    @bot.event
    async def on_raw_reaction_add(payload):
        if payload.message_id == message_id and str(payload.emoji) == emoji:
            guild = bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            await member.add_roles(role)

    @bot.event
    async def on_raw_reaction_remove(payload):
        if payload.message_id == message_id and str(payload.emoji) == emoji:
            guild = bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            await member.remove_roles(role)

    await interaction.response.send_message(f"Reaction role set up: {emoji} -> {role.name}")

@bot.tree.command(name="stop_pinging", description="Stop pinging", guild=discord.Object(id=GUILD_ID))
@commands.has_permissions(administrator=True)
async def stop_pinging(interaction: discord.Interaction):
    if bot.ping_task is not None:
        bot.ping_task.cancel()
        bot.ping_task = None
    await interaction.response.send_message("Stopped pinging")

@bot.tree.command(name="create_text_channel", description="Create a text channel", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(name="The name of the channel", category="The category to create the channel in")
@commands.has_permissions(administrator=True)
async def create_text_channel(interaction: discord.Interaction, name: str, category: discord.CategoryChannel = None):
    await interaction.guild.create_text_channel(name, category=category)
    await interaction.response.send_message(f"Created text channel {name} in category {category.name if category else 'None'}")

@bot.tree.command(name="delete_text_channel", description="Delete a text channel", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(channel="The channel to delete")
@commands.has_permissions(administrator=True)
async def delete_text_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    await channel.delete()
    await interaction.response.send_message(f"Deleted text channel {channel.name}")

@bot.tree.command(name="lock_channel", description="Lock a channel", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(channel="The channel to lock")
@commands.has_permissions(administrator=True)
async def lock_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    await channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message(f"Locked channel {channel.name}")

@bot.tree.command(name="unlock_channel", description="Unlock a channel", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(channel="The channel to unlock")
@commands.has_permissions(administrator=True)
async def unlock_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    await channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message(f"Unlocked channel {channel.name}")

   
@bot.tree.command(name="deafen", description="Deafen a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(member="The member to deafen", reason="The reason for deafening")
@commands.has_permissions(administrator=True)
async def deafen(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    await member.edit(deafen=True, reason=reason)
    await interaction.response.send_message(f"Deafened {member.mention} for: {reason}")

@bot.tree.command(name="undeafen", description="Undeafen a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(member="The member to undeafen")
@commands.has_permissions(administrator=True)
async def undeafen(interaction: discord.Interaction, member: discord.Member):
    await member.edit(deafen=False)
    await interaction.response.send_message(f"Undeafened {member.mention}")

@bot.tree.command(name="disconnect", description="Disconnect a user from a voice channel", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(member="The member to disconnect", reason="The reason for disconnecting")
@commands.has_permissions(administrator=True)
async def disconnect(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if member.voice is None:
        await interaction.response.send_message(f"{member.mention} is not in a voice channel.")
        return

    await member.move_to(None, reason=reason)
    await interaction.response.send_message(f"Disconnected {member.mention} for: {reason}")

@bot.tree.command(name="connect", description="Connect a user to a voice channel", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(member="The member to connect", channel="The voice channel to connect to", reason="The reason for connecting")
@commands.has_permissions(administrator=True)
async def connect(interaction: discord.Interaction, member: discord.Member, channel: discord.VoiceChannel, reason: str = "No reason provided"):
    if member.voice is not None:
        await interaction.response.send_message(f"{member.mention} is already in a voice channel.")
        return

    await member.move_to(channel, reason=reason)
    await interaction.response.send_message(f"Connected {member.mention} to {channel.mention} for: {reason}")

@bot.tree.command(name="move", description="Move a user to a voice channel", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(member="The member to move", channel="The voice channel to move to", reason="The reason for moving")
@commands.has_permissions(move_members=True)
@commands.has_permissions(administrator=True)
async def move(interaction: discord.Interaction, member: discord.Member, channel: discord.VoiceChannel, reason: str = "No reason provided"):
    if member.voice is None:
        await interaction.response.send_message(f"{member.mention} is not in a voice channel.")
        return

    try:
        await member.move_to(channel, reason=reason)
        await interaction.response.send_message(f"Moved {member.mention} to {channel.mention} for: {reason}")
    except discord.Forbidden:
        await interaction.response.send_message("I do not have permission to move members.")
    except discord.HTTPException as e:
        await interaction.response.send_message(f"Failed to move {member.mention}: {e}")

@bot.tree.command(name="create_channel", description="Create a voice channel", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(name="The name of the channel", category="The category to create the channel in")
@commands.has_permissions(administrator=True)
async def create_channel(interaction: discord.Interaction, name: str, category: discord.CategoryChannel = None):
    await interaction.guild.create_voice_channel(name, category=category)
    await interaction.response.send_message(f"Created voice channel {name} in category {category.name if category else 'None'}")

@bot.tree.command(name="delete_channel", description="Delete a voice channel", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(channel="The channel to delete")
@commands.has_permissions(administrator=True)
async def delete_channel(interaction: discord.Interaction, channel: discord.VoiceChannel):
    await channel.delete()
    await interaction.response.send_message(f"Deleted voice channel {channel.name}")

@bot.tree.command(name="create_category", description="Create a category", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(name="The name of the category")
@commands.has_permissions(administrator=True)
async def create_category(interaction: discord.Interaction, name: str):
    await interaction.guild.create_category(name)
    await interaction.response.send_message(f"Created category {name}")

@bot.tree.command(name="delete_category", description="Delete a category", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(category="The category to delete")
@commands.has_permissions(administrator=True)
async def delete_category(interaction: discord.Interaction, category: discord.CategoryChannel):
    await category.delete()
    await interaction.response.send_message(f"Deleted category {category.name}")

@bot.tree.command(name="create_role", description="Create a role", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(name="The name of the role", color="The color of the role (e.g., 0x1abc9c)")
@commands.has_permissions(administrator=True)
async def create_role(interaction: discord.Interaction, name: str, color: str = "0x1abc9c"):
    color = discord.Color(int(color, 16))
    await interaction.guild.create_role(name=name, color=color)
    await interaction.response.send_message(f"Created role {name} with color {color}")

@bot.tree.command(name="delete_role", description="Delete a role", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(role="The role to delete")
@commands.has_permissions(administrator=True)
async def delete_role(interaction: discord.Interaction, role: discord.Role):
    await role.delete()
    await interaction.response.send_message(f"Deleted role {role.name}")

@bot.tree.command(name="add_role", description="Add a role to a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(member="The member to add the role to", role="The role to add")
@commands.has_permissions(administrator=True)
async def add_role(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    await interaction.response.send_message(f"Added role {role.name} to {member.mention}")

@bot.tree.command(name="remove_role", description="Remove a role from a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(member="The member to remove the role from", role="The role to remove")
@commands.has_permissions(administrator=True)
async def remove_role(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    await member.remove_roles(role)
    await interaction.response.send_message(f"Removed role {role.name} from {member.mention}")

@bot.tree.command(name="create_invite", description="Create an invite", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(max_uses="The maximum number of uses for the invite", max_age="The maximum age of the invite in seconds", temporary="Whether the invite is temporary", unique="Whether the invite is unique")
@commands.has_permissions(administrator=True)
async def create_invite(interaction: discord.Interaction, max_uses: int = 0, max_age: int = 0, temporary: bool = False, unique: bool = False):
    invite = await interaction.channel.create_invite(max_uses=max_uses, max_age=max_age, temporary=temporary, unique=unique)
    await interaction.response.send_message(f"Created invite: {invite.url}")

@bot.tree.command(name="delete_invite", description="Delete an invite", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(invite="The invite code to delete")
@commands.has_permissions(administrator=True)
async def delete_invite(interaction: discord.Interaction, invite: str):
    invite_obj = await interaction.guild.invites()
    for inv in invite_obj:
        if inv.code == invite:
            await inv.delete()
            await interaction.response.send_message(f"Deleted invite {invite}")
            return
    await interaction.response.send_message(f"Invite {invite} not found")

@bot.tree.command(name="create_webhook", description="Create a webhook", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(name="The name of the webhook", avatar="The path to the avatar image file")
@commands.has_permissions(administrator=True)
async def create_webhook(interaction: discord.Interaction, name: str, avatar: str = None):
    avatar_bytes = None
    if avatar:
        with open(avatar, 'rb') as f:
            avatar_bytes = f.read()
    webhook = await interaction.channel.create_webhook(name=name, avatar=avatar_bytes)
    await interaction.response.send_message(f"Created webhook: {webhook.url}")

@bot.tree.command(name="delete_webhook", description="Delete a webhook", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(webhook_id="The webhook ID to delete")
@commands.has_permissions(administrator=True)
async def delete_webhook(interaction: discord.Interaction, webhook_id: str):
    webhook = await interaction.guild.fetch_webhook(webhook_id)
    await webhook.delete()
    await interaction.response.send_message(f"Deleted webhook {webhook_id}")

bot.run(TOKEN)