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

    @commands.command()
    @checks.is_owner()
    async def reload(self, context, module_name):
        args = [module_name]
        command = self.potato.get_command("unload")
        msg = await context.invoke(command, *args)
        await msg.delete()
        command = self.potato.get_command("load")
        await context.invoke(command, *args)

    @commands.command()
    @checks.is_owner()
    async def load(self, context, module_name):
        """Load a module."""
        resp = await self.potato.run_on_shard(None if self.potato.shard_id is None else 0, load_module, module_name)
        if resp is None:
            if self.potato.shard_id is not None:
                await self.potato.run_on_shard("all", load_module, module_name)
            return await context.send("Module loaded sucessfully.")
        else:
            msg = 'Unable to load; the module caused a `{}`:\n```py\n{}\n```'\
                .format(type(resp).__name__, self.get_traceback(resp))
            return await context.send(msg)

    @commands.command()
    @checks.is_owner()
    async def unload(self, context, module_name):
        """Unload a module."""
        resp = await self.potato.run_on_shard(None if self.potato.shard_id is None else 0, unload_module, module_name)
        if resp is None:

            if self.potato.shard_id is not None:
                await self.potato.run_on_shard("all", unload_module, module_name)
            return await context.send("Module unloaded sucessfully.")
        else:
            return await context.send("Unable to load; the module isn't loaded.")


def setup(potato):
    """Setup the Core module."""
    potato.setup_module(Core(potato))
