import discord
from discord.ext import commands
from discord import app_commands
import json
import os

INVITES_FILE = "invites.json"

def load_invites():
    if not os.path.exists(INVITES_FILE):
        with open(INVITES_FILE, "w") as f:
            json.dump({}, f)
    with open(INVITES_FILE, "r") as f:
        return json.load(f)

def save_invites(invites):
    with open(INVITES_FILE, "w") as f:
        json.dump(invites, f, indent=2)

class InviteTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invites = load_invites()
        self.cache = {}  # {guild_id: [Invite, ...]}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            self.cache[str(guild.id)] = await guild.invites()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = str(member.guild.id)
        before = self.cache.get(guild_id, [])
        after = await member.guild.invites()
        self.cache[guild_id] = after

        used = None
        for invite in after:
            for old in before:
                if invite.code == old.code and invite.uses > old.uses:
                    used = invite
                    break
            if used:
                break

        if used:
            inviter_id = str(used.inviter.id)
            if guild_id not in self.invites:
                self.invites[guild_id] = {}
            if inviter_id not in self.invites[guild_id]:
                self.invites[guild_id][inviter_id] = 0
            self.invites[guild_id][inviter_id] += 1
            save_invites(self.invites)
            # Optionally, announce in a channel:
            # channel = member.guild.system_channel
            # if channel:
            #     await channel.send(f"{member.mention} joined using {used.inviter.mention}'s invite ({used.code})!")
    
    @app_commands.command(name="invites", description="Show how many people a user has invited")
    @app_commands.describe(user="User to check (leave blank for yourself)")
    async def invites(self, interaction: discord.Interaction, user: discord.Member = None):
        user = user or interaction.user
        guild_id = str(interaction.guild.id)
        inviter_id = str(user.id)
        count = self.invites.get(guild_id, {}).get(inviter_id, 0)
        await interaction.response.send_message(f"{user.mention} has invited **{count}** member(s)!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(InviteTracker(bot))