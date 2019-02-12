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

import discord

import activityReader

from os import environ, EX_CONFIG
import mongoengine as mongo
from discord import TextChannel
from discord.ext.commands import Bot

from model import Guild
from activityReader import get_all_messages_guild, activity_logs

zero_date = datetime.datetime(year=1, month=1, day=1)

net_if = environ["NET_IF"]
mongo.connect("activity_reader", host=net_if)

try:
    BOT_TOKEN = environ["discord_api_token"]
except KeyError:
    print("Bot token not found. Please set discord_api_token in enviorment to"
          " your token.")
    exit(EX_CONFIG)

prefix = "&"
bot = Bot(prefix)
start_done = False
guild_records = {}

permission_denied = "{mention} is that command for moderators only."


async def load_guild_activity(guild, guild_record, start, end):
    """Load the user activity for a guild."""
    await activityReader.activity_logs(guild, guild_record, start, end)


def get_guild_record(guild):
    guild_record = Guild.objects.with_id(guild.id)
    if guild_record is None:
        guild_record = Guild(name=guild.name, id=guild.id)
        for member in guild.members:
            member_id = str(member.id)
            if member_id not in guild_record.last_posts:

                guild_record.last_posts[member_id] = {
                                                        "posts": 0,
                                                        "last_post": zero_date,
                                                      }
        print("Record created")
        guild_record.save()
    return guild_record


@bot.event
async def on_ready():
    """Startup sequence."""
    bot_start_time = datetime.datetime.now()
    print("Logged in as")
    print(bot.user.name)
    print(bot.user.id)
    print("------")
    last_processed_ids = {}
    for guild in bot.guilds:
        guild_record = get_guild_record(guild)
        guild_records[guild.id] = guild_record
        last_processed_ids[guild.id] = guild_record.last_processed_id

    global start_done
    start_done = True

    # Lift the lock once we have all the information needed
    for guild in bot.guilds:
        print(f"Loading {guild.name}")
        guild_record = guild_records[guild.id]
        await activity_logs(guild, guild_record, end=bot_start_time,
                            start=last_processed_ids[guild.id])
    print("Guilds loaded.")


@bot.event
async def on_message(message):
    """Update logs for incoming logs."""
    if not message.author == bot.user:
        if start_done:
            await bot.process_commands(message)
            if message.guild is not None:
                guild_id = message.guild.id
                guild_record = guild_records[guild_id]
                message_info = activityReader.get_message_info(message)
                if message_info:
                    author_id = str(message_info["id"])
                    if author_id in guild_record.last_posts:
                        guild_record.last_posts[author_id]["posts"] += 1
                        guild_record.last_posts[author_id]["last_post"] = \
                            message.created_at
                    else:
                        guild_record.last_posts[author_id] = {
                                                "last_post": message.created_at,
                                                "posts": 1,
                            }
        elif message.content.startswith(prefix):
            message_text = (f"{message.author.mention} I am not not finished"
                            " counting hold on.")
            await bot.send(message.channel, message_text)


@bot.command
async def pruge_reactions(message: discord.Message):
    """Remove all reactions from dead users."""
    channel_messages = await activityReader.get_all_messages_channel(bot,
                                                                     message
                                                                     .channel)
    for channel_message in channel_messages:
        for reaction in message.reactions:
            reactors = await bot.get_reaction_users(reaction)
            for reactor in reactors:
                if reactor not in channel_message.guild.members:
                    await channel_message.remove_reaction(reaction.emoji,
                                                          reactor)
    await bot.send(message.author, "Reaction purge complete.")
    await message.delete()


@bot.command()
async def activity_check(context, guild_id: typing.Optional[discord.Guild] = None):
    """Check all users activity."""
    if context.guild is None and guild_id is None:
        await context.author.send("check_messages requires"
                                               " a guild id in direct"
                                               " message.")
        return
    if guild_id is not None:
        for guild in bot.guilds:
            if guild.id == guild_id:
                target_guild = guild
                break
        else:
            await context.author.send(f"guild {guild_id} not found")
            return
    else:
        target_guild = context.guild

    posts = []
    non_posts = []
    guild_record = guild_records[target_guild.id]
    for member in target_guild.members:
        if not member.bot:
            member_id = str(member.id)
            if member_id not in guild_record.last_posts:
                join_date = activityReader.human_readable_date(member.joined_at)
                non_posts.append(f"**{member.mention}** has not posted."
                                 f"They join at **{join_date}**\n")
            else:
                member_record = guild_record.last_posts[member_id]
                count = member_record["posts"]
                last_post = member_record["last_post"]
                last_post_human = activityReader.human_readable_date(last_post)
                join_date = activityReader.human_readable_date(member.joined_at)
                posts.append(f"Name: **{member.mention}**"
                             f" Last Post: **{last_post_human}**"
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


@bot.command
async def delete_messages(message: discord.Message, user_id):
    """Delete all messages from a user."""
    guild = message.guild
    author = message.author
    guild_messages = await get_all_messages_guild(bot, guild)
    for guild_message in guild_messages:
        if guild_message.author.id == user_id:
            await guild_message.delete()
    await message.delete()
    await bot.send(author, "Message purge complete")


@bot.event
async def on_member_join(new_member):
    guild = new_member.guild
    guild_record = guild_records[guild]
    guild_record.last_posts[new_member] = {
                                                "posts": 0,
                                                "last_post": zero_date
                                            }


bot.run(BOT_TOKEN)
