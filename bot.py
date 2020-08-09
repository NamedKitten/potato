#!/usr/bin/python3

import argparse
import asyncio
import importlib
import logging
import os
import dill
import redis
import sys
import threading
import time
import uuid
from concurrent.futures import TimeoutError
from discord.ext import commands
from discord import utils as dutils
from utils import dataIO
import aionotify

try:
    redis_conn = redis.StrictRedis(
        host='localhost',
        port=6379,
        db=1
    )
except Exception:
    print("Couldn't connect to the redis.")
    exit(2)

settings = dataIO.load("settings")


async def send_cmd_help(ctx):
    if ctx.invoked_subcommand:
        _help = await ctx.bot.formatter.format_help_for(
            ctx,
            ctx.invoked_subcommand
        )
    else:
        _help = await ctx.bot.formatter.format_help_for(ctx, ctx.command)
    for page in _help:
        await ctx.send(page)


def prefix_getter(bot, message):
    prefixes = []
    try:
        if message.guild.id in bot.settings["prefixes"]:
            prefixes += bot.settings["prefixes"][message.guild.id]
    except:
        pass
    if type(bot.settings["command_prefix"]) is str:
        prefixes += bot.settings["command_prefix"]
    else:
        for prefix in bot.settings["command_prefix"]:
            prefixes += bot.settings["command_prefix"]
    return prefixes


class NoResponse:
    def __repr__(self):
        return '<NoResponse>'

    def __eq__(self, other):
        if isinstance(other, NoResponse):
            return True
        else:
            return False


class Potato(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = settings
        self.owner = None
        self.started = False
        self.command_prefix = prefix_getter
        self.setup_module = self.add_cog
        self.self_bot = self.settings["self_bot"]
        self.send_cmd_help = send_cmd_help
        self.send_command_help = send_cmd_help
        self.description = self.settings["description"]
        self.logger = logging.getLogger("potato")
        self.boot_time = time.time()
        self.redis = redis_conn

    def exit(code=0):
        exit(code)

    async def on_ready(self):
        if self.started:
            return
        else:
            self.started = True

        self.logger.info('Logged in as {0}.'.format(self.user))
        if self.user.bot:
            app_info = await self.application_info()
            self.invite_url = dutils.oauth_url(app_info.id)
            self.logger.info('Invite URL: {0}'.format(self.invite_url))
            self.owner = app_info.owner
        elif self.self_bot:
            self.owner = self.user
        else:
            self.owner = self.get_user(self.args.userbot)
        self.logger.info("Potato's prefixes are: " + ", ".join(self.settings["command_prefix"]))
        self.loop.create_task(self.startup())

    async def startup(self):
        self.settings["modules"].append("default.core")
        self.settings["modules"] = list(dict.fromkeys(self.settings["modules"]))
        for module in self.settings["modules"]:
            try:
                self.load_module(module)
            except Exception as e:
                self.unload_module(module)
                self.logger.warning(
                    "Module {} couldn't be loaded, {}.".format(module, e)
                )
        self.loop.create_task(self.auto_reload_modules())

    def set_module(self, module_name: str, value: bool):
        if value:
            if module_name not in self.settings["modules"]:
                self.settings["modules"].append(module_name)
        else:
            self.settings["modules"].remove(module_name)

    def load_module(self, module_name):
        self.load_extension("modules." + module_name)
        #self.extensions[module_obj.__name__] = module_obj
        self.set_module(module_name, True)
        self.logger.info("Module {} Loaded.".format(module_name))

    def unload_module(self, module_name):
        self.unload_extension("modules." + module_name)
        self.set_module(module_name, False)
        self.logger.info("Module {} Unloaded.".format(module_name))

    def reload_module(self, module_name):
        try:
            self.unload_module(module_name)
        except:
            pass
        self.load_module(module_name)

    async def _scan_for_events(self, i): 
        for event in i.event_gen():
            if type(event) is None:
                return
            if not "IN_CLOSE_NOWRITE" in event[1]:
                return
            print(list(event))

    async def auto_reload_modules(self):
        watcher = aionotify.Watcher()
        watcher.watch(alias='default', path='modules/default', flags=aionotify.Flags.MODIFY)
        watcher.watch(alias='panmodules', path='modules/panmodules', flags=aionotify.Flags.MODIFY)
        watcher.watch(alias='kitteh', path='modules/kitteh', flags=aionotify.Flags.MODIFY)
        await watcher.setup(loop)
        while True:
            event = await watcher.get_event()
            module_name = event.alias + "." + event.name.replace(".py", "")
            try:
                self.reload_module(module_name)
            except Exception as e:
                print(e)
        watcher.close()

    def __repr__(self):
        return '<Potato username={}>'.format(repr(self.user.name))


def first_time_setup():
    """Use to setup bot."""
    settings["modules"] = [
        "default.core",
        "default.general",
        "default.errors",
        "panmodules.mod",
        "default.stats",
        "panmodules.command_log",
        "default.eval",
        "default.stats"
    ]
    a = input("Do you want this bot to be a selfbot? ").lower()
    if "y" in a:
        settings["self_bot"] = True
        settings["token"] = input("Please enter your user token ")
    else:
        settings["self_bot"] = False
        settings["token"] = input("Please enter the bots token ")
    settings["command_prefix"] = input("Please enter the prefix ").split()
    settings["owners"] = []
    settings["prefixes"] = {}
    settings["roles"] = {"admin": {}, "mod": {}}
    settings["description"] = "Potato Discord Bot Framework."
    settings["setup"] = True


if not settings.get("setup", False):
    first_time_setup()


async def run():
    """Run Potato."""
    logger.info("Logging in...")
    await potato.login(
        potato.settings["token"],
        bot=not potato.settings["self_bot"]
    )
    await potato.connect()

if __name__ == '__main__':
    """Start Potato."""
    if 'clean_content' not in dir(commands):
        raise ImportError("You need discord.py rewrite to use Potato.")

    if not os.path.exists('logs'):
        os.mkdir('logs')

    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

    logger = logging.getLogger('potato')
    logger.setLevel(logging.INFO)

    handler = logging.FileHandler('logs/potato.log')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.INFO)

    handler = logging.FileHandler('logs/discord.log')
    handler.setFormatter(formatter)
    discord_logger.addHandler(handler)

    parser = argparse.ArgumentParser()
    parser.add_argument('--reset', help="Reset the bot's settings", action="store_true")
    args = parser.parse_args()

    if args.reset:
        first_time_setup()

    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        logger.info("Using uvloop.")
    except ImportError:
        logger.info('uvloop is not installed, using plain asyncio instead.')

    potato = Potato(
        None,
        self_bot=settings["self_bot"],
        pm_help=not settings["self_bot"],
    )

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run())
    except:
        logger.info("Shutting down...")
        loop.run_until_complete(potato.logout())
    finally:
        loop.close()

exit(0)
