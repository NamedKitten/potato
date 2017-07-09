from traceback import format_exception
from discord.ext import commands
from glob import glob
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
        return ''.join(format_exception(
            type(exception),
            exception,
            exception.__traceback__,
            limit=limit,
            chain=chain)
        )

    def get_modules(self):
        modules = glob("modules/**/**.py", recursive=True)
        modules = [m.replace("/", ".").replace("modules.", "").replace(".py", "") for m in modules]
        new_modules = []
        for module in modules:
            if module in self.potato.settings["modules"]:
                new_modules.append("+ " + module)
            else:
                new_modules.append("- " + module)
        return new_modules

    @commands.command()
    @checks.is_owner()
    async def reload(self, ctx, module_name):
        args = [module_name]
        command = self.potato.get_command("unload")
        msg = await ctx.invoke(command, *args)
        await msg.delete()
        command = self.potato.get_command("load")
        await ctx.invoke(command, *args)

    @commands.command()
    @checks.is_owner()
    async def load(self, ctx, module_name):
        """Load a module."""
        resp = await self.potato.run_on_shard(None if self.potato.shard_id is None else 0, load_module, module_name)
        if resp is None:
            if self.potato.shard_id is not None:
                await self.potato.run_on_shard("all", load_module, module_name)
            return await ctx.send("Module loaded sucessfully.")
        else:
            msg = 'Unable to load; the module caused a `{}`:\n```py\n{}\n```'\
                .format(type(resp).__name__, self.get_traceback(resp))
            return await ctx.send(msg)

    @commands.command()
    @checks.is_owner()
    async def unload(self, ctx, module_name):
        """Unload a module."""
        resp = await self.potato.run_on_shard(None if self.potato.shard_id is None else 0, unload_module, module_name)
        if resp is None:

            if self.potato.shard_id is not None:
                await self.potato.run_on_shard("all", unload_module, module_name)
            return await ctx.send("Module unloaded sucessfully.")
        else:
            return await ctx.send("Unable to load; the module isn't loaded.")

    @commands.command()
    @checks.is_owner()
    async def modules(self, ctx):
        """List modules."""
        modules = sorted(self.get_modules())
        message = "```diff\n"
        for module in modules:
            message += module + "\n"
        message += "```"
        await ctx.send(message)


def setup(potato):
    """Setup the Core module."""
    potato.setup_module(Core(potato))
