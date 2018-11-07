#! /usr/bin/env python3
"""
MIT License

Copyright (c) 2018 Terry Patterson

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import discord
import asyncio
import calendar
from getpass import getpass
from sys import exit
from os import environ
import datetime


client = discord.Client()


def is_welcome_message(message):
    if hasattr(message.author, "joined_at"):
        delta = message.timestamp - message.author.joined_at
        if delta.total_seconds() < 5:
            return True
    return False


def menu(question, options):
    numbered_options = list(options)
    for index, option in enumerate(numbered_options):
        question += f"\n{index} {option}"
    question += "\n"
    userResponse = int(input(question))
    return numbered_options[userResponse]


def get_user_last_post(messages):
    last_posts = {}
    with open(f"{environ['HOME']}/log.txt", mode="w") as log:
        for message in messages:
            id = message.author.id
            if not is_welcome_message(message):
                log.write(f"{message.author.name} {message.channel.name}\n")
                if id in last_posts:
                    last_posts[id]["count"] += 1
                    if last_posts[id]["last_post"] < message.timestamp:
                        last_posts[id]["last_post"] = message.timestamp
                else:
                    last_posts[id] = {
                                        "last_post": message.timestamp,
                                        "count": 1
                    }
    return last_posts


def human_readable_date(timestamp):
    month = calendar.month_name[timestamp.month]
    day = timestamp.day
    current_year = datetime.datetime.now().year
    year = timestamp.year
    if current_year == year:
        return f"{month} {day}"
    else:
        return f"{month} {day} {year}"


def write_file(last_posts, members):
    user_home = environ["HOME"]
    with open(f"{user_home}/posting_date.txt", mode="w") as file:
        lines = []
        for member in members:
            member_name = member.nick or member.name
            discriminator = member.discriminator
            if member.id in last_posts:
                last_post_date = last_posts[member.id]["last_post"]
                last_post_human = human_readable_date(last_post_date)
                total_posts = last_posts[member.id]["count"]
                lines.append(f"Name:{member_name}#{discriminator}"
                             f" Last Post: {last_post_human}"
                             f" Total Posts: {total_posts}\n")
            else:
                lines.append(f"{member_name}#{discriminator} has never "
                             "posted.\n")
        sorted_lines = sorted(lines)
        file.writelines(sorted_lines)


async def get_all_messages(channel, start=None):
    if start is None:
        start = channel.created_at
    messages = []
    async for message in client.logs_from(channel, after=start, reverse=True):
        messages.append(message)
    if len(messages) > 0:
        more_messages = await get_all_messages(channel, start=messages[-1])
        if len(more_messages) > 0:
            messages.extend(more_messages)
    return messages


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    server_query = "Which server would you like to check?"
    server = menu(server_query, client.servers)
    print(f"Processing messages for {server.name}")
    await client.request_offline_members(server)
    messages = []
    for channel in server.channels:
        if channel.permissions_for(server.me).read_messages:
            channel_messages = await get_all_messages(channel)
            messages.extend(channel_messages)
    client.close()
    last_posts = get_user_last_post(messages)
    write_file(last_posts, server.members)
    print(f"Output placed at: {environ['HOME']}/posting_date.txt")
    input("Hit enter to quit.")
    exit()


email = input("Email? ")
password = getpass()

client.run(email, password)
