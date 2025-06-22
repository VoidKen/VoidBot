import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio
import random



class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
     
    @app_commands.command(name="embed", description="Send a custom embed message")
    @app_commands.describe(
        channel="Channel to send the embed in",
        title="Embed title",
        description="Embed description",
        color="Hex color (e.g. #00ff00, optional)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def embed(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        title: str,
        description: str,
        color: str = None
    ):
        try:
            embed_color = discord.Color.default()
            if color:
                if color.startswith("#"):
                    color = color[1:]
                embed_color = discord.Color(int(color, 16))
            embed = discord.Embed(title=title, description=description, color=embed_color)
            await channel.send(embed=embed)
            await interaction.response.send_message("Embed sent!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to send embed: {e}", ephemeral=True)
    @app_commands.command(name="warn", description="Warn a user")
    @app_commands.describe(member="The member to warn", reason="The reason for warning")
    @app_commands.checks.has_permissions(administrator=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        WARNINGS_FILE = "warnings.json"
        def load_warnings():
            if os.path.exists(WARNINGS_FILE):
                with open(WARNINGS_FILE, "r") as f:
                    return json.load(f)
            return {}
        def save_warnings(warnings):
            with open(WARNINGS_FILE, "w") as f:
                json.dump(warnings, f, indent=2)
        warnings = load_warnings()
        user_id = str(member.id)
        warnings.setdefault(user_id, []).append(reason)
        save_warnings(warnings)
        await interaction.response.send_message(f"Warned {member.mention} for: {reason} (Total warnings: {len(warnings[user_id])})")

    @app_commands.command(name="clear_warnings", description="Clear all warnings for a user")
    @app_commands.describe(member="The member to clear warnings for")
    @app_commands.checks.has_permissions(administrator=True)
    async def clear_warnings(self, interaction: discord.Interaction, member: discord.Member):
        WARNINGS_FILE = "warnings.json"
        def load_warnings():
            if os.path.exists(WARNINGS_FILE):
                with open(WARNINGS_FILE, "r") as f:
                    return json.load(f)
            return {}
    

    @app_commands.command(name="poll", description="Create a poll")
    @app_commands.describe(question="The poll question", options="Comma-separated list of options")
    @app_commands.checks.has_permissions(administrator=True)
    async def poll(self, interaction: discord.Interaction, question: str, options: str):
        options_list = [option.strip() for option in options.split(',')]
        if len(options_list) < 2:
            await interaction.response.send_message("Please provide at least two options.")
            return
        embed = discord.Embed(title=question, description="\n".join([f"{chr(0x1F1E6 + i)} {option}" for i, option in enumerate(options_list)]))
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        for i in range(len(options_list)):
            await message.add_reaction(chr(0x1F1E6 + i))  # 🇦, 🇧, etc.

    @app_commands.command(name="mute", description="Mute a user")
    @app_commands.describe(member="The member to mute", reason="The reason for muting")
    @app_commands.checks.has_permissions(administrator=True)
    async def mute(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        muted_role = discord.utils.get(interaction.guild.roles, name="Muted")
        if not muted_role:
            await interaction.response.send_message("Muted role not found. Please create a 'Muted' role.")
            return
        await member.add_roles(muted_role, reason=reason)
        await interaction.response.send_message(f"Muted {member.mention} for: {reason}")

    @app_commands.command(name="unmute", description="Unmute a user")
    @app_commands.describe(member="The member to unmute")
    @app_commands.checks.has_permissions(administrator=True)
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        muted_role = discord.utils.get(interaction.guild.roles, name="Muted")
        if not muted_role:
            await interaction.response.send_message("Muted role not found. Please create a 'Muted' role.")
            return
        await member.remove_roles(muted_role)
        await interaction.response.send_message(f"Unmuted {member.mention}")

    @app_commands.command(name="kick", description="Kick a user")
    @app_commands.describe(member="The member to kick", reason="The reason for kicking")
    @app_commands.checks.has_permissions(administrator=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        await member.kick(reason=reason)
        await interaction.response.send_message(f"Kicked {member.mention} for: {reason}")

    @app_commands.command(name="ban", description="Ban a user")
    @app_commands.describe(member="The member to ban", reason="The reason for banning")
    @app_commands.checks.has_permissions(administrator=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        await member.ban(reason=reason)
        await interaction.response.send_message(f"Banned {member.mention} for: {reason}")

    @app_commands.command(name="unban", description="Unban a user")
    @app_commands.describe(member="The member to unban")
    @app_commands.checks.has_permissions(administrator=True)
    async def unban(self, interaction: discord.Interaction, member: discord.User):
        await interaction.guild.unban(member)
        await interaction.response.send_message(f"Unbanned {member.mention}")

    @app_commands.command(name="purge", description="Purge messages")
    @app_commands.describe(amount="The amount of messages to purge")
    @app_commands.checks.has_permissions(administrator=True)
    async def purge(self, interaction: discord.Interaction, amount: int):
        channel = interaction.channel
        deleted = await channel.purge(limit=amount)
        await interaction.response.send_message(f"Purged {len(deleted)} messages", ephemeral=True)

    

    @app_commands.command(name="sync", description="Sync the bot's commands globally")
    @app_commands.checks.has_permissions(administrator=True)
    async def sync(self, interaction: discord.Interaction):
     try:
        synced = await self.bot.tree.sync()  # Global sync
        await interaction.response.send_message(f"Globally synced {len(synced)} commands.")
     except Exception as e:
        await interaction.response.send_message(f"Error syncing commands: {e}")
    @app_commands.command(name="move", description="Move a member to another voice channel")
    @app_commands.describe(member="The member to move", channel="The voice channel to move the member to")
    @app_commands.checks.has_permissions(administrator=True)
    async def move(self, interaction: discord.Interaction, member: discord.Member, channel: discord.VoiceChannel):
        if member.voice is None:
            await interaction.response.send_message(f"{member.mention} is not in a voice channel.")
            return
        await member.move_to(channel)
        await interaction.response.send_message(f"Moved {member.mention} to {channel.mention}.")

    @app_commands.command(name="disconnect", description="Disconnect a member from their voice channel")
    @app_commands.describe(member="The member to disconnect from voice")
    @app_commands.checks.has_permissions(administrator=True)
    async def disconnect(self, interaction: discord.Interaction, member: discord.Member):
        if member.voice is None:
            await interaction.response.send_message(f"{member.mention} is not in a voice channel.")
            return
        await member.move_to(None)
        await interaction.response.send_message(f"Disconnected {member.mention} from their voice channel.")

    @app_commands.command(name="lock_channel", description="Lock the current channel for @everyone")
    @app_commands.checks.has_permissions(administrator=True)
    async def lock_channel(self, interaction: discord.Interaction):
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message("🔒 Channel locked for @everyone.")

    @app_commands.command(name="unlock_channel", description="Unlock the current channel for @everyone")
    @app_commands.checks.has_permissions(administrator=True)
    async def unlock_channel(self, interaction: discord.Interaction):
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = None
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message("🔓 Channel unlocked for @everyone.")
    
    @app_commands.command(name="timed_mute", description="Mute a user for a certain number of minutes")
    @app_commands.describe(member="The member to mute", minutes="How many minutes to mute for", reason="The reason for muting")
    @app_commands.checks.has_permissions(administrator=True)
    async def timed_mute(self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "No reason provided"):
        muted_role = discord.utils.get(interaction.guild.roles, name="Muted")
        if not muted_role:
            await interaction.response.send_message("Muted role not found. Please create a 'Muted' role.")
            return
        await member.add_roles(muted_role, reason=reason)
        await interaction.response.send_message(f"Muted {member.mention} for {minutes} minutes. Reason: {reason}")

        await asyncio.sleep(minutes * 60)
        # Check if user is still in the guild and still has the role
        if muted_role in member.roles:
            await member.remove_roles(muted_role)
            try:
                await member.send(f"You have been unmuted in {interaction.guild.name}.")
            except Exception:
                pass
    @app_commands.command(name="list_warnings", description="List all warnings for a user")
    @app_commands.describe(member="The member to list warnings for")
    @app_commands.checks.has_permissions(administrator=True)
    async def list_warnings(self, interaction: discord.Interaction, member: discord.Member):
        WARNINGS_FILE = "warnings.json"
        def load_warnings():
            if os.path.exists(WARNINGS_FILE):
                with open(WARNINGS_FILE, "r") as f:
                    return json.load(f)
            return {}
        warnings = load_warnings()
        user_id = str(member.id)
        user_warnings = warnings.get(user_id, [])
        if not user_warnings:
            await interaction.response.send_message(f"{member.mention} has no warnings.")
        else:
            warning_list = "\n".join(f"{idx+1}. {reason}" for idx, reason in enumerate(user_warnings))
            await interaction.response.send_message(f"Warnings for {member.mention}:\n{warning_list}")

    @app_commands.command(name="clear_warnings", description="Clear all warnings for a user")
    @app_commands.describe(member="The member to clear warnings for")
    @app_commands.checks.has_permissions(administrator=True)
    async def clear_warnings(self, interaction: discord.Interaction, member: discord.Member):
        WARNINGS_FILE = "warnings.json"
        def load_warnings():
            if os.path.exists(WARNINGS_FILE):
                with open(WARNINGS_FILE, "r") as f:
                    return json.load(f)
            return {}
        def save_warnings(warnings):
            with open(WARNINGS_FILE, "w") as f:
                json.dump(warnings, f, indent=2)
        warnings = load_warnings()
        user_id = str(member.id)
        if user_id in warnings:
            del warnings[user_id]
            save_warnings(warnings)
            await interaction.response.send_message(f"Cleared all warnings for {member.mention}.")
        else:
            await interaction.response.send_message(f"{member.mention} has no warnings to clear.")

    @app_commands.command(name="slowmode", description="Set slowmode for the current channel (in seconds)")
    @app_commands.describe(seconds="Number of seconds for slowmode (0 to disable)")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(self, interaction: discord.Interaction, seconds: int):
        if seconds < 0 or seconds > 21600:
            await interaction.response.send_message("Slowmode must be between 0 and 21600 seconds (6 hours).")
            return
        await interaction.channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            await interaction.response.send_message("Slowmode disabled for this channel.")
        else:
            await interaction.response.send_message(f"Set slowmode to {seconds} seconds for this channel.")

    @app_commands.command(name="set_nick", description="Change a member's nickname")
    @app_commands.describe(member="The member to change nickname for", nickname="The new nickname")
    @app_commands.checks.has_permissions(manage_nicknames=True)
    async def set_nick(self, interaction: discord.Interaction, member: discord.Member, nickname: str):
        try:
            await member.edit(nick=nickname)
            await interaction.response.send_message(f"Changed nickname for {member.mention} to `{nickname}`.")
        except Exception as e:
            await interaction.response.send_message(f"Failed to change nickname: {e}")

    @app_commands.command(name="reset_nick", description="Reset a member's nickname")
    @app_commands.describe(member="The member to reset nickname for")
    @app_commands.checks.has_permissions(manage_nicknames=True)
    async def reset_nick(self, interaction: discord.Interaction, member: discord.Member):
        try:
            await member.edit(nick=None)
            await interaction.response.send_message(f"Reset nickname for {member.mention}.")
        except Exception as e:
            await interaction.response.send_message(f"Failed to reset nickname: {e}")

    @app_commands.command(name="add_role", description="Add a role to a user")
    @app_commands.describe(member="The member to add the role to", role="The role to add")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def add_role(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message("I can't add a role higher or equal to my top role.", ephemeral=True)
            return
        try:
            await member.add_roles(role)
            await interaction.response.send_message(f"Added {role.mention} to {member.mention}.")
        except Exception as e:
            await interaction.response.send_message(f"Failed to add role: {e}", ephemeral=True)

    @app_commands.command(name="remove_role", description="Remove a role from a user")
    @app_commands.describe(member="The member to remove the role from", role="The role to remove")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def remove_role(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        try:
            await member.remove_roles(role)
            await interaction.response.send_message(f"Removed {role.mention} from {member.mention}.")
        except Exception as e:
            await interaction.response.send_message(f"Failed to remove role: {e}", ephemeral=True)

    @app_commands.command(name="purge_user", description="Purge a specific user's messages")
    @app_commands.describe(member="The member whose messages to purge", amount="The number of messages to check (max 100)")
    @app_commands.checks.has_permissions(administrator=True)
    async def purge_user(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if amount < 1 or amount > 100:
            await interaction.response.send_message("Amount must be between 1 and 100.", ephemeral=True)
            return
        def is_user(m):
            return m.author.id == member.id
        deleted = await interaction.channel.purge(limit=amount, check=is_user, bulk=True)
        await interaction.response.send_message(f"Purged {len(deleted)} messages from {member.mention}.", ephemeral=True)

    @app_commands.command(name="auditlog", description="Show recent moderation actions")
    @app_commands.describe(limit="Number of actions to show (max 20, default 5)")
    @app_commands.checks.has_permissions(administrator=True)
    async def auditlog(self, interaction: discord.Interaction, limit: int = 5):
        if limit < 1 or limit > 20:
            await interaction.response.send_message("Limit must be between 1 and 20.", ephemeral=True)
            return
        entries = []
        async for entry in interaction.guild.audit_logs(limit=limit):
            action = str(entry.action).split(".")[-1].replace("_", " ").title()
            target = getattr(entry.target, "mention", str(entry.target))
            user = entry.user.mention if entry.user else "Unknown"
            reason = entry.reason if entry.reason else "No reason provided"
            entries.append(f"**{action}** | Target: {target} | By: {user} | Reason: {reason}")
        if not entries:
            await interaction.response.send_message("No recent moderation actions found.", ephemeral=True)
        else:
            await interaction.response.send_message("\n".join(entries), ephemeral=True)

    @app_commands.command(name="create_role", description="Create a new role")
    @app_commands.describe(
        name="The name of the new role",
        color="Hex color (e.g. #ff0000) or leave blank for default",
        mentionable="Should the role be mentionable?"
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.has_permissions(manage_roles=True)
    async def create_role(
        self,
        interaction: discord.Interaction,
        name: str,
        color: str = None,
        mentionable: bool = False
    ):
        try:
            role_color = discord.Color.default()
            if color:
                if color.startswith("#"):
                    color = color[1:]
                role_color = discord.Color(int(color, 16))
            role = await interaction.guild.create_role(
                name=name,
                color=role_color,
                mentionable=mentionable,
                reason=f"Created by {interaction.user}"
            )
            await interaction.response.send_message(f"Role {role.mention} created!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to create role: {e}", ephemeral=True)

    @app_commands.command(name="create_text_channel", description="Create a new text channel")
    @app_commands.describe(name="The name of the new text channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def create_text_channel(self, interaction: discord.Interaction, name: str):
        try:
            channel = await interaction.guild.create_text_channel(name)
            await interaction.response.send_message(f"Text channel {channel.mention} created!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to create text channel: {e}", ephemeral=True)

    @app_commands.command(name="create_voice_channel", description="Create a new voice channel")
    @app_commands.describe(name="The name of the new voice channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def create_voice_channel(self, interaction: discord.Interaction, name: str):
        try:
            channel = await interaction.guild.create_voice_channel(name)
            await interaction.response.send_message(f"Voice channel {channel.mention} created!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to create voice channel: {e}", ephemeral=True)

    @app_commands.command(name="delete_channel", description="Delete a channel by name")
    @app_commands.describe(name="The name of the channel to delete")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def delete_channel(self, interaction: discord.Interaction, name: str):
        channel = discord.utils.get(interaction.guild.channels, name=name)
        if not channel:
            await interaction.response.send_message(f"No channel named `{name}` found.", ephemeral=True)
            return
        try:
            await channel.delete(reason=f"Deleted by {interaction.user}")
            await interaction.response.send_message(f"Channel `{name}` deleted.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to delete channel: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Admin(bot))