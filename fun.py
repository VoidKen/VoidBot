import discord
from discord.ext import commands
from discord import app_commands
import random
import aiohttp
import asyncio



class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="roast", description="Send a random roast")
    async def roast(self, interaction: discord.Interaction):
        roasts = [
            "I'd agree with you but then we'd both be wrong.",
            "If I wanted to kill myself, I'd climb your ego and jump to your IQ.",
            "You have the right to remain silent because whatever you say will probably be stupid anyway.",
            "I'm not insulting you, I'm describing you."
        ]
        await interaction.response.send_message(random.choice(roasts))
    
    
    @app_commands.command(name="wyr", description="Get a random 'Would You Rather' question")
    async def wyr(self, interaction: discord.Interaction):
        # Fallback static questions
        questions = [
            ("be able to fly", "be invisible"),
            ("live without music", "live without television"),
            ("be always hot", "be always cold"),
            ("have more time", "have more money"),
            ("speak all languages", "play all instruments"),
        ]
        q = random.choice(questions)
        question = f"Would you rather **{q[0]}** or **{q[1]}**?"
        await interaction.response.send_message(question)
    
    
    @app_commands.command(name="joke", description="Tell a random joke")
    async def joke(self, interaction: discord.Interaction):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://official-joke-api.appspot.com/random_joke") as response:
                if response.status == 200:
                    joke_data = await response.json()
                    joke = f"{joke_data['setup']} - {joke_data['punchline']}"
                    await interaction.response.send_message(joke)
                else:
                    await interaction.response.send_message("Couldn't fetch a joke at the moment, try again later.")

    @app_commands.command(name="dad_joke", description="Tell a random dad joke")
    async def dad_joke(self, interaction: discord.Interaction):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://icanhazdadjoke.com/", headers={"Accept": "application/json"}) as response:
                if response.status == 200:
                    joke_data = await response.json()
                    joke = joke_data['joke']
                    await interaction.response.send_message(joke)
                else:
                    await interaction.response.send_message("Couldn't fetch a joke at the moment, try again later.")

    @app_commands.command(name="meme", description="Get a random meme")
    async def meme(self, interaction: discord.Interaction):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.reddit.com/r/memes/random/.json") as response:
                if response.status == 200:
                    meme_data = await response.json()
                    meme_url = meme_data[0]['data']['children'][0]['data']['url']
                    await interaction.response.send_message(meme_url)
                else:
                    await interaction.response.send_message("Couldn't fetch a meme at the moment, try again later.")

    @app_commands.command(name="cat", description="Get a random cat image")
    async def cat(self, interaction: discord.Interaction):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.thecatapi.com/v1/images/search") as response:
                if response.status == 200:
                    cat_data = await response.json()
                    cat_url = cat_data[0]['url']
                    await interaction.response.send_message(cat_url)
                else:
                    await interaction.response.send_message("Couldn't fetch a cat image at the moment, try again later.")

    @app_commands.command(name="dog", description="Get a random dog image")
    async def dog(self, interaction: discord.Interaction):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.thedogapi.com/v1/images/search") as response:
                if response.status == 200:
                    dog_data = await response.json()
                    dog_url = dog_data[0]['url']
                    await interaction.response.send_message(dog_url)
                else:
                    await interaction.response.send_message("Couldn't fetch a dog image at the moment, try again later.")

    
    @app_commands.command(name="8ball", description="Ask the magic 8ball a question")
    @app_commands.describe(question="The question to ask the 8ball")
    async def eight_ball(self, interaction: discord.Interaction, question: str):
        responses = [
            "It is certain.", "It is decidedly so.", "Without a doubt.", "Yes – definitely.",
            "You may rely on it.", "As I see it, yes.", "Most likely.", "Outlook good.",
            "Yes.", "Signs point to yes.", "Reply hazy, try again.", "Ask again later.",
            "Better not tell you now.", "Cannot predict now.", "Concentrate and ask again.",
            "Don't count on it.", "My reply is no.", "My sources say no.", "Outlook not so good.", "Very doubtful."
        ]
        response = random.choice(responses)
        await interaction.response.send_message(f"🎱 {response}")

    @app_commands.command(name="trivia", description="Start a trivia game")
    async def trivia(self, interaction: discord.Interaction):
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
                        msg = await self.bot.wait_for('message', check=check, timeout=30.0)
                    except asyncio.TimeoutError:
                        await interaction.followup.send(f"Time's up! The correct answer was: {correct_answer}")
                    else:
                        if msg.content == correct_answer:
                            await interaction.followup.send("Correct! 🎉")
                        else:
                            await interaction.followup.send(f"Wrong! The correct answer was: {correct_answer}")
                else:
                    await interaction.response.send_message("Couldn't fetch a trivia question at the moment, try again later.")

    @app_commands.command(name="roll", description="Roll a dice")
    @app_commands.describe(sides="The number of sides on the dice")
    async def roll(self, interaction: discord.Interaction, sides: int = 6):
        result = random.randint(1, sides)
        await interaction.response.send_message(f"🎲 You rolled a {result} on a {sides}-sided dice")

    @app_commands.command(name="flip", description="Flip a coin")
    async def flip(self, interaction: discord.Interaction):
        result = random.choice(["Heads", "Tails"])
        await interaction.response.send_message(f"🪙 The coin landed on {result}")

    @app_commands.command(name="compliment", description="Send a random compliment")
    async def compliment(self, interaction: discord.Interaction):
        compliments = [
            "You're awesome!", "You have a great sense of humor!", "You're a true friend.",
            "You light up the room.", "You're really courageous!", "Your creativity is contagious."
        ]
        await interaction.response.send_message(random.choice(compliments))

    @app_commands.command(name="fact", description="Get a random fun fact")
    async def fact(self, interaction: discord.Interaction):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://uselessfacts.jsph.pl/random.json?language=en") as response:
                if response.status == 200:
                    data = await response.json()
                    await interaction.response.send_message(data['text'])
                else:
                    await interaction.response.send_message("Couldn't fetch a fact right now.")

    @app_commands.command(name="say", description="Make the bot say something")
    async def say(self, interaction: discord.Interaction, message: str):
        await interaction.response.send_message(message)


async def setup(bot):
    await bot.add_cog(Fun(bot))