
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
import activityReader

client =


def menu(question, options):
    numbered_options = list(options)
    for index, option in enumerate(numbered_options):
        question += f"\n{index} {option}"
    question += "\n"
    userResponse = int(input(question))
    return numbered_options[userResponse]


async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    server_query = "Which server would you like to check?"
    server = menu(server_query, bot.servers)
    print(f"Processing messages for {server.name}")
    await bot.request_offline_members(server)
    last_posts = await activityReader.activity_logs(server)
    bot.close()
    write_file(last_posts, server.members)
    print(f"Output placed at: {environ['HOME']}/posting_date.txt")
    input("Hit enter to quit.")
    exit()


def write_file(last_posts, members):
    user_home = environ["HOME"]
    with open(f"{user_home}/posting_date.txt", mode="w") as file:
        lines = []
        for member in members:
            if member.id in last_posts:
                last_post_date = last_posts[member.id]["last_post"]
                last_post_human = human_readable_date(last_post_date)
                total_posts = last_posts[member.id]["count"]
                name = last_posts[member.id]["name"]
                discriminator = last_posts[member.id]["discriminator"]

                lines.append(f"Name:{name}#{discriminator}"
                             f" Last Post: {last_post_human}"
                             f" Total Posts: {total_posts}\n")
            else:
                lines.append(f"{total_posts}#{discriminator} has never "
                             "posted.\n")
        sorted_lines = sorted(lines)
        file.writelines(sorted_lines)
        print(days)


email = input("Email? ")
password = getpass()

bot.run(email, password)
