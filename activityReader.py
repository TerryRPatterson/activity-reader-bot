#! /usr/bin/env python3
"""
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

import calendar
import datetime
from collections import OrderedDict
from os import environ
from sys import exit


def is_welcome_message(message):
    """Determine if a message is the system welcome message."""
    if hasattr(message.author, "joined_at"):
        delta = message.timestamp - message.author.joined_at
        if delta.total_seconds() < 5:
            return True
    return False


def get_message_info(message):
    """Get the information for a message."""
    id = message.author.id
    if not message.author.bot and message.author in message.server.members:
        discriminator = message.author.discriminator
        human_date = human_readable_date(message.timestamp)
        if not is_welcome_message(message):
            human_readable_join = human_readable_date(message.author.joined_at)
            return {
                                    "last_post": message.timestamp,
                                    "mention": message.author.mention,
                                    "last_post_human": human_date,
                                    "id": message.author.id,
                                    "join_date": human_readable_join,
                }

    return False


def find_last_posts(messages):
    """Find the last post for every user."""
    last_posts = {}
    for message in messages:
        info = get_message_info(message)
        if info:
            id = info["id"]
            zero_date = datetime.datetime(1, 1, 1)
            if "join_message" not in info:
                timestamp = info["last_post"]
                human_date = info["last_post_human"]
                if id in last_posts:
                    last_posts[id]["count"] += 1
                    if last_posts[id]["last_post"] < timestamp:
                        last_posts[id]["last_post"] = timestamp
                        last_posts[id]["last_post_human"] = human_date
                else:
                    last_posts[id] = {
                                        "last_post": timestamp,
                                        "count": 1,
                                        "mention": info["mention"],
                                        "last_post_human": human_date,
                                        "join_date": info["join_date"],
                    }
    return last_posts


def create_new_user(name, discriminator, join_date, last_post_human="",
                    last_post=float("-inf"), count=0):
    """Return a new user dict."""
    return {
                        "last_post": last_post,
                        "count": count,
                        "name": name,
                        "discriminator": discriminator,
                        "last_post_human": last_post_human,
                        "join_date": join_date
    }


def human_readable_date(timestamp):
    """Make the timestamp human readable."""
    month = calendar.month_name[timestamp.month]
    day = timestamp.day
    current_year = datetime.datetime.now().year
    year = timestamp.year
    if current_year == year:
        return f"{month} {day}"
    else:
        return f"{month} {day} {year}"


async def get_all_messages_channel(client, channel, start=None):
    """Get all the messages in the channel."""
    if start is None:
        start = channel.created_at
    messages = []
    done = False
    while (not done):
        new_messages = []
        async for message in client.logs_from(channel, after=start,
                                              reverse=True):
            new_messages.append(message)

        if len(new_messages) == 0:
            done = True
        else:
            start = new_messages[-1]
            messages.extend(new_messages)
    return messages

async def get_all_messages_server(client, server):
    """Retrive the full history of the server that is visible to the user."""
    messages = []
    for channel in server.channels:
        if channel.permissions_for(server.me).read_messages:
            channel_messages = await get_all_messages_channel(client, channel)
            messages.extend(channel_messages)
    return messages


async def activity_logs(client, server):
    """Get a log of all users activity."""
    messages = await get_all_messages_server(client, server)
    last_posts = find_last_posts(messages)
    sorted_last_posts = OrderedDict(sorted(last_posts.items(), key=lambda post:
                                    post[1]["last_post"]))
    return sorted_last_posts
