import discord
from discord.ext import commands
from discord import app_commands
import json
import os

NOTES_FILE = "user_notes.json"

def load_notes():
    if not os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "w") as f:
            json.dump({}, f)
    with open(NOTES_FILE, "r") as f:
        return json.load(f)

def save_notes(notes):
    with open(NOTES_FILE, "w") as f:
        json.dump(notes, f, indent=2)

class UserNotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.notes = load_notes()

    @app_commands.command(name="addnote", description="Add a private note to a user (staff only)")
    @app_commands.describe(user="User to add a note for", note="The note text")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def addnote(self, interaction: discord.Interaction, user: discord.Member, note: str):
        guild_id = str(interaction.guild.id)
        user_id = str(user.id)
        if guild_id not in self.notes:
            self.notes[guild_id] = {}
        if user_id not in self.notes[guild_id]:
            self.notes[guild_id][user_id] = []
        self.notes[guild_id][user_id].append({
            "note": note,
            "author": str(interaction.user),
            "author_id": interaction.user.id
        })
        save_notes(self.notes)
        await interaction.response.send_message(f"Note added for {user.mention}.", ephemeral=True)

    @app_commands.command(name="viewnotes", description="View all notes for a user (staff only)")
    @app_commands.describe(user="User to view notes for")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def viewnotes(self, interaction: discord.Interaction, user: discord.Member):
        guild_id = str(interaction.guild.id)
        user_id = str(user.id)
        notes = self.notes.get(guild_id, {}).get(user_id, [])
        if not notes:
            await interaction.response.send_message("No notes for this user.", ephemeral=True)
            return
        msg = "\n\n".join([f"**{i+1}.** {n['note']} *(by {n['author']})*" for i, n in enumerate(notes)])
        # Discord messages have a 2000 character limit
        if len(msg) > 1900:
            msg = msg[:1900] + "\n..."
        await interaction.response.send_message(f"Notes for {user.mention}:\n{msg}", ephemeral=True)

    @app_commands.command(name="listnotedusers", description="List all users with notes (staff only)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def listnotedusers(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        noted_ids = list(self.notes.get(guild_id, {}).keys())
        if not noted_ids:
            await interaction.response.send_message("No users with notes.", ephemeral=True)
            return
        mentions = []
        for uid in noted_ids:
            member = interaction.guild.get_member(int(uid))
            if member:
                mentions.append(member.mention)
            else:
                mentions.append(f"<@{uid}>")
        await interaction.response.send_message("Users with notes:\n" + ", ".join(mentions), ephemeral=True)

async def setup(bot):
    await bot.add_cog(UserNotes(bot))