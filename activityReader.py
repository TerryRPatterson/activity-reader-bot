"""
Functions for retrive messages and generating activity reports.

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

from discord.utils import snowflake_time
import mongoengine as mdb
from model import Server


def is_welcome_message(message):
    """Determine if a message is the system welcome message."""
    if hasattr(message.author, "joined_at"):
        delta = message.timestamp - message.author.joined_at
        if delta.total_seconds() < 5:
            return True
    return False


def get_message_info(message):
    """Get the information for a message."""
    if not message.author.bot and message.author in message.server.members:
        info = {
                                "last_post": message.timestamp,
                                "id": message.author.id,
            }
        if is_welcome_message(message):
            info["join_message"] = True

        return info
    return False


def find_last_posts(messages, server_record):
    """Find the last post for every user."""
    server_last_post_time = snowflake_time(server_record.last_processed_id)
    last_processed_id = server_record.last_processed_id
    for message in messages:
        message_time = snowflake_time(message.id)
        if server_last_post_time < message_time:
            last_processed_id = message.id
            server_last_post_time = message_time
        info = get_message_info(message)
        if info:
            id = info["id"]
            if "join_message" not in info:
                timestamp = info["last_post"]
                if id in server_record.last_posts:
                    server_record.last_posts[id]["posts"] += 1
                    if server_record.last_posts[id]["last_post"] < timestamp:
                        server_record.last_posts[id]["last_post"] = timestamp
                else:

                    server_record.last_posts[id] = {
                                                        "posts": 1,
                                                        "last_post": timestamp,
                                                    }
    return last_processed_id


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


async def get_all_messages_channel(client, channel, start=None, end=None):
    """Get all the messages in the channel."""
    if start is None:
        start = channel.created_at
    messages = []
    done = False
    while (not done):
        done = True
        async for message in client.logs_from(channel, after=start,
                                              reverse=True):
            count += 1
            if end is not None and message.timestamp >= end:
                done = True
                break
            yield message
        else:
            done = False


async def get_all_messages_server(client, server, start=None, end=None):
    """Retrive the full history of the server that is visible to the user."""
    messages = []
    for channel in server.channels:
        if channel.permissions_for(server.me).read_messages:
            channel_messages = await get_all_messages_channel(client, channel,
                                                              start, end)
            messages.extend(channel_messages)
    return messages


async def activity_logs(client, server, server_record, start, end):
    """Get a log of all users activity."""
    messages = await get_all_messages_server(client, server, start, end)
    server_record.last_processed_id = find_last_posts(messages, server_record)
    server_record.save()
