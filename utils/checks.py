import discord
from discord.ext import commands
from __main__ import potato, settings


def owner_check(ctx):
    if ctx.message.author.id == potato.owner.id:
        return True
    elif ctx.message.author.id in settings["owners"]:
        return True
    return False


def is_owner():
    return commands.check(owner_check)


def is_bot_account():
    def predicate(ctx):
        return ctx.bot.user.bot
    return commands.check(predicate)


def is_not_bot_account():
    def predicate(ctx):
        return not ctx.bot.user.bot
    return commands.check(predicate)


def is_selfbot():
    def predicate(ctx):
        return ctx.bot.self_bot
    return commands.check(predicate)


def is_not_selfbot():
    def predicate(ctx):
        return not ctx.bot.self_bot
    return commands.check(predicate)


def is_main_shard():
    def predicate(ctx):
        if ctx.bot.shard_id is None:
            return True
        elif ctx.bot.shard_id == 0:
            return True
        else:
            return False
    return commands.check(predicate)


def is_not_main_shard():
    def predicate(ctx):
        if ctx.bot.shard_id is None:
            return False
        elif ctx.bot.shard_id == 0:
            return False
        else:
            return True
    return commands.check(predicate)


def mod_or_permissions(**permissions):
    def predicate(ctx):
        if owner_check(ctx):
            return True
        if not isinstance(ctx.message.author, discord.Member):
            return False
        if ctx.message.author == ctx.message.guild.owner:
            return True
        # let's get the roles and compare them to
        # what we have on file (if we do)
        roles = [x.name.lower() for x in ctx.message.author.roles]
        try:
            if settings['roles']["mod"][ctx.guild.id].lower() in roles:
                return True
        except KeyError:
            pass
        try:
            if settings['roles']["admin"][ctx.guild.id].lower() in roles:
                return True
        except KeyError:
            pass
        user_permissions = dict(
            ctx.message.author.permissions_in(
                ctx.message.channel
            ))
        for permission in permissions:
            if permissions[permission]:
                allowed = user_permissions.get(permission, False)
                if allowed:
                    return True
        return False
    return commands.check(predicate)


def admin_or_permissions(**permissions):
    def predicate(ctx):
        if owner_check(ctx):
            return True
        if not isinstance(ctx.message.author, discord.Member):
            return False
        if ctx.message.author == ctx.message.guild.owner:
            return True
        try:
            roles = [x.name.lower() for x in ctx.message.author.roles]
            if settings['roles']['admin'][ctx.guild.id].lower() in roles:
                return True
        except KeyError:
            pass
        user_permissions = dict(
            ctx.message.author.permissions_in(
                ctx.message.channel
            ))
        for permission in permissions:
            if permissions[permission]:
                allowed = user_permissions.get(permission, False)
                if allowed:
                    return True
        return False
    return commands.check(predicate)


def serverowner_or_permissions(**permissions):
    def predicate(ctx):
        if owner_check(ctx):
            return True
        if not isinstance(ctx.message.author, discord.Member):
            return False
        if ctx.message.author == ctx.message.guild.owner:
            return True
        user_permissions = dict(
            ctx.message.author.permissions_in(
                ctx.message.channel
            ))
        for permission in permissions:
            allowed = user_permissions.get(permission, False)
            if allowed:
                return True
        return False
    return commands.check(predicate)


serverowner = serverowner_or_permissions
admin = admin_or_permissions
mod = mod_or_permissions
