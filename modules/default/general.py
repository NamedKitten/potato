import aiohttp
import time
import datetime
import discord
from discord.ext import commands
from utils import checks


class General:
    def __init__(self, potato):
        self.potato = potato

    @commands.group(invoke_without_command=True)
    async def set(self, ctx):
        """Set command group."""
        return await self.potato.send_command_help(ctx)

    @set.command("admin")
    @checks.serverowner()
    async def admin(self, ctx, *, role_name: str):
        """Set Admin role for current server."""
        if role_name not in [a.name for a in ctx.guild.roles]:
            return await ctx.send("Role couldn't be found")
        self.potato.settings["roles"]["admin"][ctx.guild.id] = role_name
        return await ctx.send("Admin role has been set.")

    @set.command("mod")
    @checks.serverowner()
    async def mod(self, ctx, *, role_name: str):
        """Set Mod role for current server."""
        if role_name not in [a.name for a in ctx.guild.roles]:
            return await ctx.send("Role couldn't be found")
        self.potato.settings["roles"]["mod"][ctx.guild.id] = role_name
        return await ctx.send("Mod role has been set.")

    @set.command("owners")
    @checks.is_owner()
    async def owners(self, ctx, *, owners: str):
        """Set owners using a space seperated list of IDs."""
        try:
            owners = [int(a) for a in owners.split()]
        except:
            return await ctx.send("Owner IDs must be ints.")
        self.potato.settings["owners"] = owners
        return await ctx.send("Owners have been set.")

    @set.group(invoke_without_command=True)
    async def prefix(self, ctx):
        """Set command prefix."""
        return await self.potato.send_command_help(ctx)

    @prefix.command("global")
    async def global_prefix(self, ctx, *, prefixes):
        """Set global command prefix."""
        self.potato.settings["command_prefix"] = prefixes.split()
        await ctx.send("Prefix has been set.")

    @prefix.command("server")
    async def guild_prefix(self, ctx, *, prefixes):
        """Set server-wide prefix."""
        self.potato.settings["prefixes"][ctx.guild.id] = prefixes.split()
        await ctx.send("Prefix has been set.")

    @set.command("name")
    @checks.is_owner()
    async def name(self, ctx, username: str):
        """Changes Potato's username."""
        await self.potato.user.edit(username=username)
        await ctx.send('My name is now {0}.'.format(username))

    #  Taken from Liara.
    @set.command("avatar")
    @checks.is_owner()
    async def avatar(self, ctx, url: str):
        """Changes Potato's avatar."""
        session = aiohttp.ClientSession()
        response = await session.get(url)
        avatar = await response.read()
        response.close()
        await session.close()
        try:
            await self.potato.user.edit(avatar=avatar)
            await ctx.send('Done!')
        except discord.errors.InvalidArgument:
            await ctx.send('That image type is unsupported.')

    # Taken from Liara.
    @staticmethod
    async def timeit(coro):
        """Times a coroutine."""
        before = time.monotonic()
        coro_result = await coro
        after = time.monotonic()
        return after - before, coro_result

    # Taken from Liara.
    @staticmethod
    def format_delta(delta):
        return round(delta * 1000)

    # Taken from Liara.
    @commands.command()
    async def ping(self, ctx):
        """Pong!"""
        before = time.monotonic()
        typing_delay = self.format_delta((await self.timeit(ctx.trigger_typing()))[0])
        message_delay, message = await self.timeit(ctx.send('..'))
        message_delay = self.format_delta(message_delay)
        edit_delay = self.format_delta((await self.timeit(message.edit(content='...')))[0])
        gateway_delay = self.format_delta((await self.timeit(await self.potato.ws.ping()))[0])
        after = time.monotonic()
        total_delay = self.format_delta(after - before)
        await message.edit(content='Typing delay: `{}ms`\nMessage send delay: `{}ms`\n'
                                   'Message edit delay: `{}ms`\nGateway delay: `{}ms`\nTotal: `{}ms`'
                                   .format(typing_delay, message_delay, edit_delay, gateway_delay, total_delay))

    # Taken from Liara.
    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def userinfo(self, ctx, user: discord.Member=None):
        """Shows you a user's info. """

        if user is None:
            member = ctx.message.author
        else:
            member = user

        if member.status == discord.Status.online:
            status = 'Online'
        elif member.status == discord.Status.idle:
            status = 'Away'
        elif member.status == discord.Status.do_not_disturb:
            status = 'DnD'
        else:
            status = 'Offline'

        embed = discord.Embed()
        embed.title = '{} {}'.format(status, member)
        avatar_url = member.avatar_url.replace('webp', 'png')
        embed.description = '**Display name**: {0.display_name}\n**ID**: {0.id}\n[Avatar]({1})'\
                            .format(member, avatar_url)

        if member.game is not None:
            embed.description += '\
            **Game**: {}'.format(member.game.__str__())

        join_delta = datetime.datetime.utcnow() - member.joined_at
        created_delta = datetime.datetime.utcnow() - member.created_at
        embed.add_field(name='Join Dates', value='**This server**: {} ago ({})\n**Discord**: {} ago ({})'
                        .format(join_delta, member.joined_at, created_delta, member.created_at))

        roles = [x.mention for x in sorted(
            member.roles,
            key=lambda role: role.position
        ) if not x.is_default()]
        roles.reverse()
        if roles:
            if len(str(roles)) < 1025:
                embed.add_field(name='Roles', value=', '.join(roles))
        embed.set_thumbnail(url=avatar_url.replace('size=1024', 'size=256'))

        if ctx.channel.permissions_for(ctx.guild.me).embed_links:
            if ctx.author.id == self.potato.user.id:
                await ctx.message.edit(embed=embed)
            else:
                await ctx.send(embed=embed)
        else:
            await ctx.send(
                "Unable to post userinfo,\
                please allow the Embed Links permission."
            )

    # Taken from Liara.
    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def serverinfo(self, ctx):
        """Shows you the server's info."""
        guild = ctx.guild

        embed = discord.Embed()
        embed.title = str(guild)
        if guild.icon_url is not None:
            embed.description = '**ID**: {0.id}\
            [Icon URL]({0.icon_url})'.format(guild)
            embed.set_thumbnail(url=guild.icon_url)
        else:
            embed.description = '**ID**: {0.id}'.format(guild)

        embed.add_field(name='Members', value=guild.member_count)

        roles = [x.mention for x in guild.role_hierarchy if not x.is_default()]
        if roles:
            roles = ', '.join(roles)
            if len(roles) <= 1024:
                embed.add_field(name='Roles', value=roles)

        channels = [x[1] for x in sorted(
            [
                (x.position, x.mention) for x in guild.channels if isinstance(
                    x,
                    discord.TextChannel
                )]
        )]
        channels = ', '.join(channels)
        if len(channels) <= 1024:
            embed.add_field(name='Text channels', value=channels)

        if guild.verification_level == discord.VerificationLevel.none:
            verification_level = 'None'
        elif guild.verification_level == discord.VerificationLevel.low:
            verification_level = 'Low'
        elif guild.verification_level == discord.VerificationLevel.medium:
            verification_level = 'Medium'
        else:
            verification_level = '(╯°□°）╯︵ ┻━┻'

        if guild.explicit_content_filter == discord.ContentFilter.disabled:
            explicit_level = 'Don\'t scan any messages'
        elif guild.explicit_content_filter == discord.ContentFilter.no_role:
            explicit_level = 'Scan messages from members without a role'
        else:
            explicit_level = 'Scan messages sent by all members'

        info = '**AFK channel**: {0.afk_channel}\n**AFK timeout**: {0.afk_timeout} seconds\n' \
               '**Owner**: {0.owner.mention}\n**Region**: `{0.region.value}`\n' \
               '**Verification level**: {1}\n**Explicit content filter**: {2}'.format(guild, verification_level,
                                                                                      explicit_level)

        embed.add_field(name='Other miscellaneous info', value=info)

        embed.timestamp = guild.created_at
        embed.set_footer(text='Created on')

        if ctx.channel.permissions_for(ctx.guild.me).embed_links:
            if ctx.author.id == self.potato.user.id:
                await ctx.message.edit(embed=embed)
            else:
                await ctx.send(embed=embed)
        else:
            await ctx.send('Unable to post serverinfo,\
            please allow the Embed Links permission.')

    @commands.command(aliases=["logout", "die"])
    async def shutdown(self, context, exit_code: int=0):
        self.potato.logger.error("Exiting with code " + str(exit_code))
        exit(exit_code)


def setup(potato):
    """Setup the General module."""
    n = General(potato)
    potato.setup_module(n)
