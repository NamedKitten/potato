from traceback import format_exception
from discord.ext import commands
from glob import glob
from utils import checks

class Core(commands.Cog):
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

    def get_modules_list(self):
        modules = glob("modules/**/**.py", recursive=True)
        modules = [m.replace("/", ".").replace("modules.", "").replace(".py", "") for m in modules]
        return modules

    def get_modules(self):
        modules = self.get_modules_list()
        new_modules = []
        for module in modules:
            if module in self.potato.settings["modules"]:
                new_modules.append("+ " + module)
            else:
                new_modules.append("- " + module)
        return new_modules

    def get_full_module_name(self, name):
        modules = self.get_modules_list()
        for module in self.get_modules_list():
            if module.endswith(name):
                return module
        return name

    @commands.command()
    @checks.is_owner()
    async def reload(self, ctx, module_name):
        await self.unload(ctx, module_name)
        await self.load(ctx, module_name)

    @commands.command()
    @checks.is_owner()
    async def load(self, ctx, module_name):
        """Load a module."""
        module_name = self.get_full_module_name(module_name)
        try:
            self.potato.load_module(module_name)
            return await ctx.send("Module loaded sucessfully.")
        except Exception as e:
            msg = 'Unable to load; the module caused a `{}`:\n```py\n{}\n```'\
                .format(type(e).__name__, self.get_traceback(e))
            return await ctx.send(msg)

    @commands.command()
    @checks.is_owner()
    async def unload(self, ctx, module_name):
        """Unload a module."""
        module_name = self.get_full_module_name(module_name)
        try:
            self.potato.unload_module(module_name)
            return await ctx.send("Module unloaded sucessfully.")
        except Exception as e:
            return await ctx.send("Unable to load; the module isn't loaded.")

    @commands.command()
    @checks.is_owner()
    async def modules(self, ctx):
        """List modules."""
        modules = sorted(self.get_modules())
        message = "```diff\n"
        message += "\n".join(modules)
        message += "```"
        await ctx.send(message)


def setup(potato):
    """Setup the Core module."""
    potato.setup_module(Core(potato))
