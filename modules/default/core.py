import traceback
from discord.ext import commands
from utils import checks


def load_module(potato, module_name):
    return potato.load_module(module_name)


def unload_module(potato, module_name):
    return potato.unload_module(module_name)


class Core:
    def __init__(self, potato):
        self.potato = potato

    @staticmethod
    def get_traceback(exception, limit=None, chain=True):
        return ''.join(traceback.format_exception(
            type(exception),
            exception,
            exception.__traceback__,
            limit=limit,
            chain=chain)
        )

    @commands.command(aliases=["reload"])
    @checks.is_owner()
    async def load(self, context, module_name):
        """Load a module."""
        resp = await self.potato.run_on_shard(None if self.potato.shard_id is None else 0, load_module, module_name)
        if resp is None:
            msg = "Module loaded sucessfully."
            if self.potato.shard_id is not None:
                for shard in range(1, self.potato.shard_count):
                    self.potato.loop.create_task(self.potato.run_on_shard(shard, load_module, module_name))
        else:
            msg = 'Unable to load; the module caused a `{}`:\n```py\n{}\n```'\
                .format(type(resp).__name__, self.get_traceback(resp))
        await context.send(msg)

    @commands.command()
    @checks.is_owner()
    async def unload(self, context, module_name):
        """Unload a module."""
        resp = await self.potato.run_on_shard(None if self.potato.shard_id is None else 0, unload_module, module_name)
        if resp is None:
            msg = "Module unloaded sucessfully."
            if self.potato.shard_id is not None:
                for shard in range(1, self.potato.shard_count):
                    self.potato.run_on_shard(shard, unload_module, module_name)
        else:
            msg = "Unable to load; the module isn't loaded."
        await context.send(msg)


def setup(potato):
    """Setup the Core module."""
    n = Core(potato)
    potato.setup_module(n)
