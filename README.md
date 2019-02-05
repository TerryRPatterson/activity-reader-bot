# Introduction
Activity Reader Bot is a discord bot that automates administrative
tasks.

# Usage
Activty Reader bot requires docker installed to use.
To start the bot
- Export your bot token as an enviorment variable
named `discord_api_token`.
- Run `build_container --prod`
- Run `start --prod`


This will start the bot and begin counting
all message in the server. Counting will take longer depending on how
many messages are in the servers the bot is a member of. The bot will
not acknowledge commands during the messsage counting.

# Commands
  ## `&activity_check`
  Displays a report on the activity for all users on the server.
  The output will look like:
```shell
Name: @Terryp Last Post: February 2 Join date: November 5 2018 Total Posts: 106
```
## `&purge_reactions`
Remove all reactions in the current channel for users who are no longer
in the server

## `&delete_messages {user id}`
Deletes all messages from the user specified by the id. This includes
join messages provided by discord.

# Development
To start development you need docker installed. Then:
- Export your bot token as an enviorment variable
named `discord_api_token`.
- Run `build_container`
- Run `start`

This will start the bot with the git repository mounted into the
container. Build container is not needed when the python files are
changes, kill the bot and run `start` again.

##Style Guide
-   Code should comply with pep8

-   Functions should be documented wiht doc-strings complaint with [pep-257](https://www.python.org/dev/peps/pep-0257/), and using [Googles
recommaned arugement syntax
](https://google.github.io/styleguide/pyguide.html?#38-comments-and-docstrings)

-   Executable files should begin with a shebang line using the
`#! /usr/bin/env Executable` style.
