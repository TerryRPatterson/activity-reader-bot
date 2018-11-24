#! /usr/bin/env python3

import discord
import activityReader
from api_secrets import bot_token
from discord_bot_framework.discord_bot import Bot


bot = Bot(title="ActivityChecker", prefix="&")
finished_processing = False
server_activity_logs = {}


async def load_server_activity(server):
    await bot.request_offline_members(server)
    last_posts = await activityReader.activity_logs(bot, server)
    server_activity_logs[server.id] = last_posts
    return last_posts


@bot.event
async def on_ready():
    """"Startup sequence."""
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    for server in bot.servers:
        print(f"Loading {server.name}")
        server_log = await load_server_activity(server)
        server_activity_logs[server.id] = server_log
    print("Servers loaded.")
    global finished_processing
    finished_processing = True


@bot.event
async def on_message(message):
    """Update logs for incoming logs."""
    if finished_processing:
        await bot.process_message(message)
        server_id = message.server.id
        server_log = server_activity_logs[server_id]
        message_info = activityReader.get_message_info(message)
        if message_info:
            author_id = message_info["id"]
            if author_id in server_log:
                author_log = server_log[author_id]
                message_info["count"] = author_log["count"] + 1
            else:
                message_info["count"] = 1
            print(message_info)
            server_log[author_id] = message_info


@bot.command
@bot.admin
async def activity_check(message: discord.Message):
    """Check all users activity."""
    target_channel = message.channel
    target_server = message.server
    lines = []
    server_logs = server_activity_logs[target_server.id]
    for user in server_logs.values():
        lines.append(f"Name:{user['name']}#{user['discriminator']}"
                     f" Last Post: {user['last_post_human']}"
                     f" Total Posts: {user['count']}\n")
    message_text = ""
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

bot.run(bot_token)
