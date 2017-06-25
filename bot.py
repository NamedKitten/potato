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
    def __init__(self, command_prefix, **kwargs):
        super().__init__(command_prefix, **kwargs)
        self.settings = settings
        self.owner = None
        self.command_prefix = prefix_getter
        self.setup_module = self.add_cog
        self.self_bot = self.settings["self_bot"]
        self.send_cmd_help = send_cmd_help
        self.send_command_help = send_cmd_help
        self.description = self.settings["description"]
        self.logger = logging.getLogger("potato")
        self.boot_time = time.time()
        self.redis = redis_conn
        self._pubsub_futures = {}  # futures temporarily stored here
        self._pubsub_broadcast_cache = {}
        db = str(self.redis.connection_pool.connection_kwargs['db'])
        self.pubsub_id = 'potato.{}.pubsub.code'.format(db)
        threading.Thread(name='pubsub', target=self._pubsub_loop, daemon=True).start()
        threading.Thread(name='pubsub cache', target=self._pubsub_cache_loop, daemon=True).start()

    def exit(code=0):
        exit(code)

    async def on_ready(self):
        try:
            import pyfiglet
            for line in pyfiglet.figlet_format("potato", "3D-ASCII").splitlines():
                self.logger.info(line)
        except:
            pass

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
        if self.shard_id is not None:
            self.logger.info('Shard {0} of {1}.'.format(self.shard_id + 1, self.shard_count))
        self.loop.create_task(self.startup())

    async def startup(self):
        for module in self.settings["modules"]:
            try:
                self.load_module(module)
            except:
                self.unload_module(module)
                self.logger.warning(
                    "Module {} couldn't be loaded.".format(module)
                )

    def set_module(self, module_name: str, value: bool):
        if value:
            if module_name not in self.settings["modules"]:
                self.settings["modules"].append(module_name)
        else:
            self.settings["modules"].remove(module_name)

    def load_module(self, module_name):
        module_obj = importlib.import_module("modules." + module_name)
        importlib.reload(module_obj)
        module_obj.setup(self)
        self.extensions[module_obj.__name__] = module_obj
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

    def _process_pubsub_event(self, event):
        _id = self.pubsub_id
        if event['type'] != 'message':
            return
        try:
            _data = dill.loads(event['data'])
            target = _data.get('target')
            broadcast = target == 'all'
            if not isinstance(_data, dict):
                return
            # get type, if this is a broken dict just ignore it
            if _data.get('type') is None:
                return
            # ping response
            if target == self.shard_id or broadcast:
                if _data['type'] == 'ping':
                    self.redis.publish(_id, dill.dumps({'type': 'response', 'id': _data.get('id'),
                                                        'response': 'Pong.'}))
                if _data['type'] == 'coderequest':
                    func = _data.get('function')  # get the function, discard if None
                    if func is None:
                        return
                    resp = {'type': 'response', 'id': _data.get('id'), 'response': None}
                    if broadcast:
                        resp['from'] = self.shard_id
                    args = _data.get('args', ())
                    kwargs = _data.get('kwargs', {})
                    try:
                        resp['response'] = func(self, *args, **kwargs)  # this gets run in a thread so whatever
                    except Exception as e:
                        resp['response'] = e
                    try:
                        self.redis.publish(_id, dill.dumps(resp))
                    except dill.PicklingError:  # if the response fails to dill, return None instead
                        resp = {'type': 'response', 'id': _data.get('id')}
                        if broadcast:
                            resp['from'] = self.shard_id
                        self.redis.publish(_id, dill.dumps(resp))
            if _data['type'] == 'response':
                __id = _data.get('id')
                _from = _data.get('from')
                if __id is None:
                    return
                if __id not in self._pubsub_futures:
                    return
                if __id not in self._pubsub_broadcast_cache and _from is not None:
                    return
                if _from is None:
                    self._pubsub_futures[__id].set_result(_data.get('response'))
                    del self._pubsub_futures[__id]
                else:
                    self._pubsub_broadcast_cache[__id][_from] = _data.get('response')

        except dill.UnpicklingError:
            return

    def _pubsub_loop(self):
        pubsub = self.redis.pubsub()
        _id = self.pubsub_id
        pubsub.subscribe(_id)
        for event in pubsub.listen():
            threading.Thread(target=self._process_pubsub_event, args=(event,), name='pubsub event', daemon=True).start()

    def _pubsub_cache_loop(self):
        while True:
            for k, v in dict(self._pubsub_broadcast_cache).items():
                contents = [v[x] for x in v if x != 'expires']
                if v['expires'] < time.monotonic() or NoResponse() not in contents:
                    del v['expires']
                    self._pubsub_futures[k].set_result(v)
                    del self._pubsub_futures[k]
                    del self._pubsub_broadcast_cache[k]
            time.sleep(0.01)  # be nice to the host

    def request(self, target, broadcast_timeout=1, **kwargs):
        _id = str(uuid.uuid4())
        self._pubsub_futures[_id] = fut = asyncio.Future()
        request = {'id': _id, 'target': target}
        request.update(kwargs)
        if target == 'all':
            cache = {k: NoResponse() for k in range(0, self.shard_count)}  # prepare the cache
            cache['expires'] = time.monotonic() + broadcast_timeout
            self._pubsub_broadcast_cache[_id] = cache
        self.redis.publish(self.pubsub_id, dill.dumps(request))
        return fut

    async def run_on_shard(self, shard, func, *args, **kwargs):
        return await self.request(shard, type='coderequest', function=func, args=args, kwargs=kwargs)

    async def ping_shard(self, shard, timeout=1):
        try:
            await asyncio.wait_for(self.request(shard, type='ping'), timeout=timeout)
            return True
        except TimeoutError:
            return False

    def __repr__(self):
        return '<Potato username={} shard_id={} shard_count={}>'.format(
            *[repr(x) for x in [self.user.name, self.shard_id, self.shard_count]])


def first_time_setup():
    """Use to setup bot."""
    settings["modules"] = [
        "default.core",
        "default.general",
        "default.errors",
        "default.mod",
        "default.stats"
    ]
    a = input("Do you want this bot to be a selfbot? ").lower()
    if "y" in a:
        settings["self_bot"] = True
        settings["token"] = input("Please enter your user token ")
    else:
        settings["self_bot"] = False
        settings["token"] = input("Please enter the bots token ")
    settings["command_prefix"] = input("Please enter the prefix ")
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

    shard_grp = parser.add_argument_group('sharding')
    shard_grp.add_argument('--shard_id', type=int, help='the shard ID the bot should run on', default=None)
    shard_grp.add_argument('--shard_count', type=int, help='the total number of shards you are planning to run',
                           default=None)
    args = parser.parse_args()

    if args.shard_id is not None:  # usability
        args.shard_id -= 1

    if args.reset:
        first_time_setup()

    def warn():
        logger.warning(
            "Windows is NOT supported."
            "No support will be provided."
        )
    if sys.platform == 'win32':
        warn()
    if sys.platform == 'linux':
        if os.path.exists('/dev/lxss'):
            warn()
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        logger.info("Using uvloop.")
    except ImportError:
        logger.info('uvloop is not installed, using plain asyncio instead.')

    potato = Potato(
        settings["command_prefix"],
        self_bot=settings["self_bot"],
        pm_help=not settings["self_bot"],
        shard_id=args.shard_id,
        shard_count=args.shard_count,
    )

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        loop.run_until_complete(potato.logout())
    finally:
        loop.close()

exit(0)
