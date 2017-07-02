import aiohttp
import time
import discord
from discord.ext import commands
from utils import checks


class General:
    def __init__(self, potato):
        self.potato = potato

    @commands.group(invoke_without_command=True)
    async def set(self, ctx):
        """Set command group."""
        return await self.potato.send_command_help(ctx)

    @set.command("admin")
    @checks.serverowner()
    async def admin(self, ctx, *, role_name: str):
        """Set Admin role for current server."""
        if role_name not in [a.name for a in ctx.guild.roles]:
            return await ctx.send("Role couldn't be found")
        self.potato.settings["roles"]["admin"][ctx.guild.id] = role_name
        return await ctx.send("Admin role has been set.")

    @set.command("mod")
    @checks.serverowner()
    async def mod(self, ctx, *, role_name: str):
        """Set Mod role for current server."""
        if role_name not in [a.name for a in ctx.guild.roles]:
            return await ctx.send("Role couldn't be found")
        self.potato.settings["roles"]["mod"][ctx.guild.id] = role_name
        return await ctx.send("Mod role has been set.")

    @set.command("owners")
    @checks.is_owner()
    async def owners(self, ctx, *, owners: str):
        """Set owners using a space seperated list of IDs."""
        try:
            owners = [int(a) for a in owners.split()]
        except:
            return await ctx.send("Owner IDs must be ints.")
        self.potato.settings["owners"] = owners
        return await ctx.send("Owners have been set.")

    @set.group(invoke_without_command=True)
    async def prefix(self, ctx):
        """Set command prefix."""
        return await self.potato.send_command_help(ctx)

    @prefix.command("global")
    async def global_prefix(self, ctx, *prefixes: str):
        """Set global command prefix."""
        self.potato.settings["command_prefix"] = prefixes
        await ctx.send("Prefix has been set.")

    @prefix.command("server")
    async def guild_prefix(self, ctx, *prefixes: str):
        """Set server-wide prefix."""
        self.potato.settings["prefixes"][ctx.guild.id] = prefixes
        await ctx.send("Prefix has been set.")

    @set.command("name")
    @checks.is_owner()
    async def name(self, ctx, username: str):
        """Changes Potato's username."""
        await self.potato.user.edit(username=username)
        await ctx.send('My name is now {0}.'.format(username))

    #  Taken from Liara.
    @set.command("avatar")
    @checks.is_owner()
    async def avatar(self, ctx, url: str):
        """Changes Potato's avatar."""
        session = aiohttp.ClientSession()
        response = await session.get(url)
        avatar = await response.read()
        response.close()
        await session.close()
        try:
            await self.potato.user.edit(avatar=avatar)
            await ctx.send('Done!')
        except discord.errors.InvalidArgument:
            await ctx.send('That image type is unsupported.')

    # Taken from Liara.
    @staticmethod
    async def timeit(coro):
        """Times a coroutine."""
        before = time.monotonic()
        coro_result = await coro
        after = time.monotonic()
        return after - before, coro_result

    # Taken from Liara.
    @staticmethod
    def format_delta(delta):
        return round(delta * 1000)

    # Taken from Liara.
    @commands.command()
    async def ping(self, ctx):
        """Pong!"""
        before = time.monotonic()
        typing_delay = self.format_delta((await self.timeit(ctx.trigger_typing()))[0])
        message_delay, message = await self.timeit(ctx.send('..'))
        message_delay = self.format_delta(message_delay)
        edit_delay = self.format_delta((await self.timeit(message.edit(content='...')))[0])
        gateway_delay = self.format_delta((await self.timeit(await self.potato.ws.ping()))[0])
        after = time.monotonic()
        total_delay = self.format_delta(after - before)
        await message.edit(content='Typing delay: `{}ms`\nMessage send delay: `{}ms`\n'
                                   'Message edit delay: `{}ms`\nGateway delay: `{}ms`\nTotal: `{}ms`'
                                   .format(typing_delay, message_delay, edit_delay, gateway_delay, total_delay))

    @commands.command(aliases=["logout", "die"])
    async def shutdown(self, context, exit_code: int=0):
        self.potato.logger.error("Exiting with code " + str(exit_code))
        exit(exit_code)

    @commands.command()
    async def info(self, context):
        await context.send(
            "This bot uses the rewrite version of the discord.py library and "
            "uses the Potato bot framework made by NamedKitten#8468 ( <@305058659799400448> ).\n" +
            "Discord.py: https://github.com/Rapptz/discord.py/tree/rewrite\n"
            "Potato: https://github.com/NamedKitten/potato"
        )


def setup(potato):
    """Setup the General module."""
    n = General(potato)
    potato.setup_module(n)
