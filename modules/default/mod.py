import discord
from discord.ext import commands
from utils import checks


class Mod:
    def __init__(self, potato):
        self.potato = potato

    def __local_check(self, ctx):
        return commands.guild_only()

    @commands.command()
    @checks.mod_or_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, days: int=1):
        """Ban a member."""
        if not 0 <= days <= 7:
            await ctx.send('Invalid number of days. Use a number from 0 to 7.')
            return
        try:
            await member.ban(delete_message_days=days)
            await ctx.send('Bye! \u270B')
        except discord.Forbidden:
            await ctx.send("Sorry,\
                I must not have permissions to ban this member.\
            ")

    @commands.command()
    @checks.mod_or_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member):
        """Kick a member."""
        try:
            await member.kick()
            await ctx.send('Done!')
        except discord.Forbidden:
            await ctx.send('I must not have permissions to kick this member.')


def setup(potato):
    n = Mod(potato)
    potato.setup_module(n)
