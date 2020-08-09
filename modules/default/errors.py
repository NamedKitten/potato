import traceback
from discord.ext import commands
from discord.ext.commands import errors as commands_errors

from utils import chat_formatting as cf


class Errors(commands.Cog):
    def __init__(self, potato):
        self.potato = potato
        potato.on_command_error = self.on_command_error

    @staticmethod
    def get_traceback(exception, limit=None, chain=True):
        return ''.join(traceback.format_exception(
            type(exception),
            exception,
            exception.__traceback__,
            limit=limit,
            chain=chain)
        )

    async def on_command_error(self, context, exception):
        if isinstance(exception, commands_errors.MissingRequiredArgument):
            await context.send(
                cf.warning("You are missing a required argument!")
            )
            await self.potato.send_cmd_help(context)
            return
        elif isinstance(exception, commands_errors.BadArgument):
            await context.send(cf.warning("Bad argument!"))
            await self.potato.send_command_help(context)
        elif isinstance(exception, commands_errors.CommandInvokeError):
            exception = exception.original
            _traceback = traceback.format_tb(exception.__traceback__)
            _traceback = ''.join(_traceback)
            error = '`{0}` in command `{1}`: ```py\n{2}```'.format(
                type(exception).__name__,
                context.command.qualified_name,
                _traceback
            )
            print(error)
            await context.send(cf.warning(error))
        elif isinstance(exception, commands_errors.CheckFailure):
            print(exception, dir(exception), repr(exception), str(exception))
            await context.send(
                cf.warning(
                    f"{exception.args[0]}"
                )
            )
        elif isinstance(exception, commands_errors.CommandOnCooldown):
            await context.send(
                cf.warning(
                    "You are being ratelimited, \n"
                    "Please try again in {:.2f}s.".format(
                        exception.retry_after
                    )
                )
            )
        else:
            await context.send(cf.warning('`{}`:\n```py\n{}\n```'.format(
                type(exception).__name__, self.get_traceback(exception))))
        for line in self.get_traceback(exception).splitlines():
            self.potato.logger.error(line)


def setup(potato):
    n = Errors(potato)
    potato.setup_module(n)
