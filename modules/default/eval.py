import aiohttp
import json
import textwrap
import time
import traceback

import discord
from discord.ext import commands
from utils import checks


class Eval(commands.Cog):
    def __init__(self, potato):
        self.potato = potato
        self._eval = {}

    @staticmethod
    async def create_gist(content, filename='output.py'):
        github_file = {'files': {filename: {'content': str(content)}}}
        async with aiohttp.ClientSession() as session:
            async with session.post('https://api.github.com/gists', data=json.dumps(github_file)) as response:
                return await response.json()

    @commands.command()
    @checks.is_owner()
    async def eval(self, ctx, *, code: str):
        """Evaluates Python code."""
        if self._eval.get('env') is None:
            self._eval['env'] = {}
        if self._eval.get('count') is None:
            self._eval['count'] = 0

        self._eval['env'].update({
            'self': self,
            'bot': self.potato,
            'potato': self.potato,
            'ctx': ctx,
            'message': ctx.message,
            'channel': ctx.message.channel,
            'guild': ctx.message.guild,
            'author': ctx.message.author,
        })

        code = code.replace('```py\n', '').replace('```', '').replace('`', '')

        _code = 'async def func(self):\n  try:\n{}\n  finally:\n    self._eval[\'env\'].update(locals())'\
            .format(textwrap.indent(code, '    '))

        before = time.monotonic()
        try:
            exec(_code, self._eval['env'])

            func = self._eval['env']['func']
            output = await func(self)

            if output is not None:
                output = repr(output)
        except Exception as e:
            t = ""
            for line in traceback.format_exception(type(e), e, e.__traceback__):
                t += line
            output = '{}: {}\n{}'.format(type(e).__name__, e, t)
        after = time.monotonic()
        self._eval['count'] += 1
        count = self._eval['count']

        code = code.split('\n')
        if len(code) == 1:
            _in = 'In [{}]: {}'.format(count, code[0])
        else:
            _first_line = code[0]
            _rest = code[1:]
            _rest = '\n'.join(_rest)
            _countlen = len(str(count)) + 2
            _rest = textwrap.indent(_rest, '...: ')
            _rest = textwrap.indent(_rest, ' ' * _countlen)
            _in = 'In [{}]: {}\n{}'.format(count, _first_line, _rest)

        message = '```py\n{}'.format(_in)
        if output is not None:
            message += '\nOut[{}]: {}'.format(count, output)
        ms = int(round((after - before) * 1000))
        if ms > 100:
            message += '\n# {} ms\n```'.format(ms)
        else:
            message += '\n```'

        try:
            if ctx.author.id == self.potato.user.id:
                await ctx.message.edit(content=message)
            else:
                await ctx.send(message)
        except discord.HTTPException:
            await ctx.trigger_typing()
            gist = await self.create_gist(message, filename='message.md')
            await ctx.send('Sorry, that output was too large, so I uploaded it to gist instead.\n'
                           '{0}'.format(gist['html_url']))

def setup(potato):
    potato.setup_module(Eval(potato))
