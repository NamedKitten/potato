import aiohttp
import json
import asyncio
import datetime
import platform

import random
from discord.ext import commands

from utils import checks

try:
    import tabulate
    import psutil
except ImportError:
    raise RuntimeError('tabulate and psutil are required for this cog')

tabulate.MIN_PADDING = 0  # makes for a neater table


def gather_info(potato):
    return {'guilds': len(potato.guilds),
            'members': len(set(potato.get_all_members())), 'up_since': potato.boot_time,
            'messages_seen': potato.get_cog('Sharding').messages, 'host': platform.node().lower(),
            'memory': psutil.Process().memory_full_info().uss / 1024**2,
            'host_uptime': psutil.boot_time()}


def _halt(potato):
    potato.loop.create_task(potato.logout())


class Sharding:
    def __init__(self, potato):
        self.potato = potato
        self.lines = []
        self.messages = 0

    async def on_message(self, _):
        self.messages += 1

    @commands.group(invoke_without_command=True)
    async def shards(self, ctx):
        """A bunch of sharding-related commands."""
        await self.potato.send_command_help(ctx)

    async def get_line(self):
        if not self.lines:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://gist.githubusercontent.com/Pandentia/373f23a4443e4c363b653777f296301e/'
                                       'raw/0fd0a31891bf9e3ea59c1a5d9e739579d6dab714/sims_loading_lines.json') as resp:
                    self.lines = json.loads(await resp.text())
        return '*{}...*'.format(random.choice(self.lines))

    async def edit_task(self, message):
        while True:
            await asyncio.sleep(random.randint(2, 4))
            await message.edit(content=await self.get_line())

    @shards.command()
    async def list(self, ctx, mode='generic'):
        """Lists all shards.
        * mode: "generic" or "host"
        Arguments marked with * are optional.
        """
        if mode.lower() not in ('generic', 'host'):
            await ctx.send('Invalid mode.')
            return await self.potato.send_command_help(ctx)

        msg = await ctx.send(await self.get_line())
        task = self.potato.loop.create_task(self.edit_task(msg))
        shards = {}
        for shard in range(0, self.potato.shard_count):
            status = await self.potato.ping_shard(shard)
            shards[shard+1] = status
        for shard, status in dict(shards).items():
                shards[shard] = await self.potato.run_on_shard(shard-1, gather_info)

        table = []
        if mode == 'generic':
            table = [['Active', 'Shard', 'Guilds', 'Members', 'Messages', ]]
            for shard, state in shards.items():
                line = ['*' if shard - 1 == self.potato.shard_id else '', shard,
                        state.get('guilds', ''),
                        state.get('members', ''),
                        state.get('messages_seen', '')]
                table.append(line)
        if mode == 'host':
            table = [['Active', 'Shard', 'Host', 'Memory', 'Up Since', 'Host Up Since']]
            for shard, state in shards.items():
                line = ['*' if shard - 1 == self.potato.shard_id else '', shard,
                        state.get('host', ''),
                        state.get('memory', ''),
                        datetime.datetime.utcfromtimestamp(state.get('up_since', 0)) if state.get('up_since') else '',
                        datetime.datetime.utcfromtimestamp(state.get('host_uptime', 0)) if state.get('host_uptime')
                        else '']
                table.append(line)
        table = '```prolog\n{}\n```'.format(
            tabulate.tabulate(table, tablefmt='psql', headers='firstrow'))
        task.cancel()
        await msg.edit(content=table)

    @shards.command()
    async def get(self, ctx):
        """Gets the current shard."""
        await ctx.send('I am shard {} of {}.'.format(self.potato.shard_id+1, self.potato.shard_count))

    @shards.command(aliases=['shutdown'])
    @checks.is_owner()
    async def halt(self, ctx, shard: int):
        """Halts a shard.
        - shard: The shard you want to halt
        """
        active = await self.potato.ping_shard(shard-1)
        if not active:
            return await ctx.send('Shard not online.')
        await self.potato.run_on_shard(shard-1, _halt)
        await ctx.send('Halt command sent.')

    @shards.command()
    @checks.is_owner()
    async def halt_all(self, ctx):
        """Halts all shards."""
        msg = await ctx.send(await self.get_line())
        task = self.potato.loop.create_task(self.edit_task(msg))

        shards = []
        for shard in range(0, self.potato.shard_count):
            state = await self.potato.ping_shard(shard)
            if state and shard != self.potato.shard_id:
                shards.append(shard)

        for shard in shards:
            await self.potato.run_on_shard(shard, _halt)
        task.cancel()
        await msg.edit(content='Thank you for using potato.')
        await self.potato.run_on_shard(self.potato.shard_id, _halt)


def setup(potato):
    if potato.shard_id is not None:
        potato.add_cog(Sharding(potato))
    else:
        raise RuntimeError('this cog requires your bot to be sharded')
