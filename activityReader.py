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
from asyncio import wait, create_task
from discord import Forbidden, HTTPException
from time import sleep

backoff = 60


def get_message_info(message):
    """Get the information for a message."""
    if not message.author.bot:
        info = {
                                "last_post": message.created_at,
                                "id": message.author.id,
            }

        return info
    return False


def process_post(message, guild_record):
    info = get_message_info(message)

    if info:
        id = info["id"]
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


async def get_all_messages_channel(guild, channel, start, end):
    messages = []
    try:
        async for message in channel.history(after=start,
                                             oldest_first=True,
                                             before=end,
                                             limit=None):
            messages.append(message)
        return messages
    except (Forbidden, AttributeError):
        return messages
    except HTTPException as e:
        if e.status == 503:
            global backoff
            print(f'503 exception backing off for {backoff}')
            sleep(backoff)
            backoff * 2
            return get_all_messages_channel(guild, channel, start, end)


async def get_all_messages_guild(guild, start=None, end=None):
    """Retrive the full history of the guild that is visible to the user."""
    if isinstance(start, int):
        start = snowflake_time(start)
    if isinstance(end, int):
        end = snowflake_time(end)
    channels = []
    for channel in guild.channels:
        channel_coro = get_all_messages_channel(guild, channel, start, end)
        channel_task = create_task(channel_coro)
        channels.append(channel_task)

    done, pending = await wait(channels)

    messages = []
    for task in done:
        messages.extend(task.result())
    return messages


async def activity_logs(guild, guild_record, start, end):
    """Get a log of all users activity."""
    messages = await get_all_messages_guild(guild, start, end)
    for message in messages:
        process_post(message, guild_record)
