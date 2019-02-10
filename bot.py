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

import activityReader
import discord
from os import environ, EX_CONFIG
import mongoengine as mongo

from model import Server
from activityReader import get_all_messages_server
from discord import Game as RichStatus, Status
from discord_bot import Bot

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
bot = Bot(title="ActivityChecker", prefix=prefix)
start_done = False
server_records = {}

permission_denied = "{mention} is that command for moderators only."


async def load_server_activity(server, server_record, start, end):
    """Load the user activity for a server."""
    await bot.request_offline_members(server)
    await activityReader.activity_logs(bot, server, server_record, start, end)


def get_server_record(server):
    server_record = Server.objects.with_id(server.id)
    if server_record is None:
        server_record = Server(name=server.name, id=server.id)
        for member in server.members:
            if member.id not in server_record.last_posts:

                server_record.last_posts[member.id] = {
                                                        "posts": 0,
                                                        "last_post": zero_date,
                                                      }
        print("Record created")
        server_record.save()
    return server_record


@bot.event
async def on_ready():
    """Startup sequence."""
    bot_start_time = datetime.datetime.now()
    await bot.set_state(text="Counting all new messages.",
                        status="do_not_disturb")
    print("Logged in as")
    print(bot.user.name)
    print(bot.user.id)
    print("------")
    last_processed_ids = {}
    for server in bot.servers:
        server_record = get_server_record(server)
        server_records[server.id] = server_record
        last_processed_ids[server.id] = server_record.last_processed_id

    global start_done
    start_done = True

    # Lift the lock once we have all the information needed
    for server in bot.servers:
        print(f"Loading {server.name}")
        server_record = server_records[server.id]
        await load_server_activity(server, server_record, end=bot_start_time,
                                   start=last_processed_ids[server.id])
    print("Servers loaded.")

    await bot.set_state()


@bot.event
async def on_message(message):
    """Update logs for incoming logs."""
    if not message.author == bot.user:
        if start_done:
            await bot.process_message(message)
            if message.server is not None:
                server_id = message.server.id
                server_record = server_records[server_id]
                message_info = activityReader.get_message_info(message)
                if message_info:
                    author_id = message_info["id"]
                    if author_id in server_record.last_posts:
                        server_record.last_posts[author_id]["posts"] += 1
                        server_record.last_posts[author_id]["last_post"] = \
                            message.timestamp
                    else:
                        server_record.last_posts[author_id] = {
                                                "last_post": message.timestamp,
                                                "posts": 1,
                            }
        elif message.content.startswith(prefix):
            message_text = (f"{message.author.mention} I am not not finished"
                            " counting hold on.")
            await bot.send_message(message.channel, message_text)


@bot.permissions_required(permissions=["manage_messages"],
                          check_failed=permission_denied)
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
                if reactor not in channel_message.server.members:
                    await bot.remove_reaction(channel_message, reaction.emoji,
                                              reactor)
    await bot.send_message(message.author, "Reaction purge complete.")
    await bot.delete_message(message)


@bot.permissions_required(permissions=["kick_members"],
                          check_failed=permission_denied)
@bot.command
async def activity_check(message: discord.Message,
                         server_id: "optional" = None):
    """Check all users activity."""
    if message.server is None and server_id is None:
        await bot.send_message(message.author, "check_messages requires"
                                               " a server id in direct"
                                               " message.")
        return
    if server_id is not None:
        for server in bot.servers:
            if server.id == server_id:
                target_server = server
                break
        else:
            await bot.send_message(message.author,
                                   f"Server {server_id} not found")
            return
    else:
        target_server = message.server

    target_channel = message.channel

    posts = []
    non_posts = []
    server_record = server_records[target_server.id]
    for member in target_server.members:
        if not member.bot:
            if member.id not in server_record.last_posts:
                join_date = activityReader.human_readable_date(member.joined_at)
                non_posts.append(f"**{member.mention}** has not posted."
                                 f"They join at **{join_date}**\n")
            else:
                member_record = server_record.last_posts[member.id]
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
            await bot.send_message(target_channel, message_text)
            message_text = line
        elif index + 1 == total_lines:
            await bot.send_message(target_channel, new_message_text)
        else:
            message_text = new_message_text


@bot.permissions_required(permissions=["manage_messages"],
                          check_failed=permission_denied)
@bot.command
async def delete_messages(message: discord.Message, user_id):
    """Delete all messages from a user."""
    server = message.server
    author = message.author
    server_messages = await get_all_messages_server(bot, server)
    for server_message in server_messages:
        if server_message.author.id == user_id:
            await bot.delete_message(server_message)
    await bot.delete_message(message)
    await bot.send_message(author, "Message purge complete")


@bot.event
async def on_member_join(new_member):
    server = new_member.server
    server_record = server_records[server]
    server_record.last_posts[new_member] = {
                                                "posts": 0,
                                                "last_post": zero_date
                                            }


bot.run(BOT_TOKEN)
