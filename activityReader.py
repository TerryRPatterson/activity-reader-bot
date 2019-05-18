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

from contextlib import AsyncExitStack
from discord import TextChannel
from discord.utils import snowflake_time


def is_welcome_message(message):
    """Determine if a message is the system welcome message."""
    if hasattr(message.author, "joined_at"):
        delta = message.created_at - message.author.joined_at
        if delta.total_seconds() < 5:
            return True
    return False


def get_message_info(message):
    """Get the information for a message."""
    if not message.author.bot and message.author in message.guild.members:
        info = {
                                "last_post": message.created_at,
                                "id": message.author.id,
            }
        if is_welcome_message(message):
            info["join_message"] = True

        return info
    return False


def process_post(message, guild_record, last_processed):
    message_time = message.created_at
    if last_processed < message_time:
        last_processed = message.id
        last_processed = message_time
    info = get_message_info(message)
    if info:
        id = info["id"]
        if "join_message" not in info:
            timestamp = info["last_post"]
            if id in guild_record.last_posts:
                guild_record.last_posts[id]["posts"] += 1
                if guild_record.last_posts[id]["last_post"] < timestamp:
                    guild_record.last_posts[id]["last_post"] = timestamp
            else:

                guild_record.last_posts[id] = {
                                                    "posts": 1,
                                                    "last_post": timestamp,
                                                }
    return last_processed


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


async def get_all_messages_guild(guild, start=None, end=None):
    """Retrive the full history of the guild that is visible to the user."""
    if type(start) == int:
        start = snowflake_time(start)
    if type(end) == int:
        end = snowflake_time(end)
    for channel in guild.channels:
        if isinstance(channel, TextChannel):
            if channel.permissions_for(guild.me).read_messages:
                async for message in channel.history(after=start,
                                                     oldest_first=True,
                                                     before=end,
                                                     limit=None):
                    yield message


async def activity_logs(guild, guild_record, start, end):
    """Get a log of all users activity."""
    last_processed = guild_record.last_processed
    async for message in get_all_messages_guild(guild, start, end):
        guild_record.last_processed = process_post(message, guild_record,
                                                   last_processed)
    guild_record['last_posts'].set_modified()
    await guild_record.commit()
