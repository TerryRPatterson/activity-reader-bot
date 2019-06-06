#! /usr/bin/env python3
"""
The main bot logic of activity reader.

Copyright 2018 Terry Patterson

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
import datetime
import typing
import asyncio
import re

import discord
import aiohttp


import activityReader

from os import environ, EX_CONFIG
from concurrent.futures import ThreadPoolExecutor
from sys import stdin, exit

from discord.ext.commands import Bot, is_owner
from discord.errors import NotFound
from box import Box

from activityReader import (get_all_messages_guild, activity_logs,
                            human_readable_date)
from Guild import Guild



loop = asyncio.get_event_loop()

zero_date = datetime.datetime(year=2015, month=1, day=1)

pool = ThreadPoolExecutor()


def command_handler():
    command = stdin.readline()
    command = command.strip()
    if command != 'exit':
        print(f'Unknown command {command}')
        return
    write_guild_file(guild_records)
    exit()



with open('key') as f:
    BOT_TOKEN = f.read().strip()

prefix = "&"
bot = Bot(prefix, loop=loop)
start_done = False
guild_records = Box()

permission_denied = "{mention} is that command for moderators only."


async def load_guild_activity(guild, guild_record, start, end):
    """Load the user activity for a guild."""
    await activity_logs(guild, guild_record, start, end)


def load_guild_file():
    try:
        with open('guilds.yaml') as file:
            return Box.from_yaml(file.read())
    except FileNotFoundError:
        return Box()


def write_guild_file(records):
    with open('guilds.yaml', 'w') as file:
        file.write(records.to_yaml())


@bot.event
async def on_ready():
    """Startup sequence."""
    bot_start_time = datetime.datetime.now()
    print("Logged in as")
    print(bot.user.name)
    print(bot.user.id)
    print("------")
    last_processeds = {}
    global guild_records
    guild_records = await loop.run_in_executor(pool, load_guild_file)
    for guild in bot.guilds:
        default = Guild(guild.name, guild.id)
        guild_record = guild_records.setdefault(guild.id, default)
        last_processeds[guild.id] = guild_record.last_processed
    write_guild_file(guild_records)

    global start_done
    start_done = True

    # Lift the lock once we have all the information needed
    for guild in bot.guilds:
        print(f"Loading {guild.name}")
        guild_record = guild_records[guild.id]
        guild_last_post_time = guild_record.last_processed
        await activity_logs(guild, guild_record, end=bot_start_time,
                            start=guild_last_post_time)
    print("Guilds loaded.")


@bot.event
async def on_message(message):
    """Update logs for incoming logs."""
    if not message.author == bot.user:
        if start_done:
            with message.channel.typing():
                await bot.process_commands(message)
                if message.guild is not None:
                    guild_id = message.guild.id
                    guild_record = guild_records[guild_id]
                    message_info = activityReader.get_message_info(message)
                    if message_info:
                        author_id = message_info["id"]
                        if author_id in guild_record.last_posts:
                            guild_record.last_posts[author_id]["posts"] += 1
                            guild_record.last_posts[author_id]["last_post"] = \
                                message.created_at
                        else:
                            guild_record.last_posts[author_id] = {
                                                    "last_post":
                                                    message.created_at,
                                                    "posts": 1,
                                }
        elif message.content.startswith(prefix):
            message_text = (f"{message.author.mention} I am not not finished"
                            " counting hold on.")
            await message.channel.send(message_text)


@bot.command()
async def purge_reactions(context):
    """Remove all reactions from dead users."""
    async for channel_message in context.history(limit=None):
        for reaction in channel_message.reactions:
            async for reactor in reaction.users():
                if reactor not in channel_message.guild.members:
                    await channel_message.remove_reaction(reaction.emoji,
                                                          reactor)
    await context.author.send("Reaction purge complete.")
    await context.message.delete()


@bot.command()
async def activity_check(context,
                         guild_id: typing.Optional[int] = None):
    """Check all users activity."""
    if context.guild is None and context is None:
        await context.author.send("check_messages requires"
                                  " a guild id in direct"
                                  " message.")
        return

    if guild_id is None:
        target_guild = context.guild
    else:
        target_guild = bot.get_guild(guild_id)
        if target_guild is None:
            message = (f"{context.author.mention} I am sorry I could not find "
                       f"guild {guild_id}")
            await context.send(message)
            return

    guild_record = guild_records[target_guild.id]
    last_posts = guild_record.last_posts
    sorted_last_posts = sorted(last_posts.items(), key=lambda post:
                               post[1]["last_post"])
    sorted_last_posts = dict(sorted_last_posts)

    non_posting_members = (member for member in target_guild.members 
                                if not member.id in sorted_last_posts)

    non_posting_members_non_bot = (member for member in non_posting_members
                                        if not member.bot)

    non_posts = []
    for member in non_posting_members_non_bot:
        print(f"{member.name} was not found in last posts")
        join_date = human_readable_date(member.joined_at)
        non_posts.append(f"**{member.mention}** has not posted."
                        f"They join at **{join_date}**\n")

    posts = []
    for member_id, member_record in sorted_last_posts.items():
        member = target_guild.get_member(member_id)
        if member is not None and not member.bot:
            count = member_record["posts"]
            if count == 0:
                join_date = human_readable_date(member.joined_at)
                non_posts.append(f"**{member.mention}** has not posted."
                                    f"They join at **{join_date}**\n")
            else:
                last_post = member_record["last_post"]
                last_post_human = human_readable_date(last_post)
                join_date = human_readable_date(member.joined_at)
                posts.append(f"Last Post: **{last_post_human}**"
                                f" Name: **{member.mention}**"
                                f" Join date: **{join_date}**"
                                f" Total Posts: **{count}**\n")

    message_text = ""
    lines = non_posts + posts
    total_lines = len(lines)
    for index, line in enumerate(lines):
        new_message_text = message_text + line
        if len(new_message_text) > 2000:
            await context.send(message_text)
            message_text = line
        elif index + 1 == total_lines:
            await context.send(new_message_text)
        else:
            message_text = new_message_text


def purge_messages_target(target_guild):
    return lambda message: message.author not in target_guild.members


@bot.command()
async def purge_messages(context):
    """Delete all messages from users no longer present in the server."""
    guild = context.guild
    async with context.typing():
        delete_gen = _delete_messages(guild, purge_messages_target(guild))
        title_text = f"Deleting messages for {guild.name}"
        embed_args = {
            "title": title_text,
            "done_message": "Purge complete"
        }
        await counter_messages(delete_gen, context, embed_args)
        await context.message.delete()


def delete_messages_by_target(target):
    return lambda message: message.author.id == target


@bot.command()
async def delete_messages_by(context, target: int, name=None):
    """Delete all messages from a user."""
    guild = context.guild
    async with context.typing():
        delete_gen = _delete_messages(guild, delete_messages_by_target(target))
        member = guild.get_member(target)
        target_user = bot.get_user(target)
        if member is not None:
            name = member.nick is not None if member.nick else member.name
            title_text = f"Deleting messages for {name}"
        elif target_user is not None:
            title_text = f"Deleting messages for {target_user.name}"
        else:
            title_text = f"Deleting messages for {target}"
        embed_args = {
            "title": title_text,
            "done_message": "Purge complete"
        }
        await counter_messages(delete_gen, context, embed_args)
        await context.message.delete()


async def _delete_messages(guild, target_func):
    read = 0
    deleted = 0
    major_read = 0
    async for guild_message in get_all_messages_guild(guild):
        read += 1
        if read % 100 == 0:
            major_read = read
            fields = {'Messages Read': major_read, 'Messages Delete': deleted}
            yield (False, fields)
        if target_func(guild_message):
            print(guild_message.author.name)
            await guild_message.delete()
            deleted += 1
            fields = {'Messages Read': major_read, 'Messages Deleted': deleted}
            yield (False, fields)
    else:
        fields = {'Messages Read': read, 'Messages Delete': deleted}
        yield (False, fields)
        yield (True, None)


async def counter_messages(gen, target, embed_args={}):
    done_message = embed_args.pop('done_message', None)
    embed = discord.Embed(**embed_args)
    embeded_message = await target.send(embed=embed)
    async for done, value in gen:
        if done:
            if embed:
                name = 'Completion Message:'
                embed.add_field(name=name, value=done_message, inline=False)
                await embeded_message.edit(embed=embed)
                return (value, embed)
            return value
        else:
            fields = value
        embed = discord.Embed(**embed_args)
        for name, value in fields.items():
            embed.add_field(name=name, value=value)
        else:
            await embeded_message.edit(embed=embed)


@bot.event
async def on_member_join(new_member):
    guild = new_member.guild
    guild_record = guild_records[guild.id]
    guild_record.last_posts[new_member.id] = {
                                                "posts": 0,
                                                "last_post": zero_date
                                            }

@is_owner()
@bot.command()
async def get_emoji(context, start: int, end: int):
    emoji_regex = re.compile('^<:(?P<name>[\\w]+?):(?P<id>\\d+)>$')
    animated_emoji_regex = re.compile('^<a:(?P<name>[\\w]+?):(?P<id>\\d+)>$')

    for channel in context.guild.text_channels:
        try:
            after = await channel.fetch_message(start)
            before = await channel.fetch_message(end)
            target_channel = after.channel

            break
        except NotFound:
            pass

    async with aiohttp.ClientSession() as session:
        async for message in target_channel.history(limit=None, before=before,
                                                    after=after):
            emoji_match = emoji_regex.match(message.content)
            animated_emoji_match = animated_emoji_regex.match(message.content)
            if emoji_match is not None:

                id = emoji_match.group('id')
                name = emoji_match.group('name')
                await upload_emoji(id, name, session, context.guild)

            elif animated_emoji_match is not None:
                id = animated_emoji_match.group('id')
                name = animated_emoji_match.group('name')
                await upload_emoji(id, name, session, context.guild, 'gif')

async def upload_emoji(id, name, session, guild, type='png'):
    url = f'https://cdn.discordapp.com/emojis/{id}.{type}'
    async with session.get(url) as resp:
        if resp.status == 200:
            image = await resp.read()
            await guild.create_custom_emoji(name=name,
                                                    image=image)


def start():
    loop.add_reader(stdin.fileno(), command_handler)
    bot.run(BOT_TOKEN)

if __name__ == "__main__":
    start()
