import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import io
import datetime

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="profile", description="Show your Discord profile card")
    @app_commands.describe(user="The user to show (leave blank for yourself)")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        user = user or interaction.user

        # Fetch avatar
        async with aiohttp.ClientSession() as session:
            async with session.get(user.display_avatar.url) as resp:
                avatar_bytes = await resp.read()
        avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((128, 128))

        # Create card
        card = Image.new("RGBA", (400, 180), (54, 57, 63, 255))
        draw = ImageDraw.Draw(card)
        font_big = ImageFont.truetype("arial.ttf", 28)
        font_small = ImageFont.truetype("arial.ttf", 18)

        # Paste avatar
        card.paste(avatar, (20, 26), avatar)

        # Draw username
        draw.text((170, 30), f"{user.display_name}", font=font_big, fill=(255, 255, 255))
        draw.text((170, 70), f"Joined: {user.joined_at.strftime('%Y-%m-%d')}", font=font_small, fill=(200, 200, 200))
        draw.text((170, 100), f"ID: {user.id}", font=font_small, fill=(200, 200, 200))

        # Roles (excluding @everyone)
        roles = [r.name for r in user.roles if r.name != "@everyone"]
        roles_text = ", ".join(roles) if roles else "No roles"
        draw.text((170, 130), f"Roles: {roles_text}", font=font_small, fill=(180, 180, 255))

        # Save to buffer
        buf = io.BytesIO()
        card.save(buf, format="PNG")
        buf.seek(0)

        file = discord.File(buf, filename="profile.png")
        embed = discord.Embed(title=f"{user.display_name}'s Profile", color=discord.Color.blue())
        embed.set_image(url="attachment://profile.png")
        await interaction.response.send_message(embed=embed, file=file)

async def setup(bot):
    await bot.add_cog(Profile(bot))