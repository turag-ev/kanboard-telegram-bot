# kanboard-telegram-bot
is a [Telegram-Bot](https://core.telegram.org/bots) with Kanboard and permission features.
It's main purpose is the ability to provide a interface for your [Kanboard](https://github.com/kanboard/) via the [Kanboard-API](https://docs.kanboard.org/en/latest/api/index.html).
While Telegram-Bots are generally open for everyone, the bot provides security/permission features.

# Usage


# Installation
I assume, that you're a Telegram-User and have your own Kanboard installed.
Please install the following:

## Telegram-Bot for Python
https://python-telegram-bot.org/

## Kanboard for Python
https://pypi.org/project/kanboard/

## Additional Packages

> pip install requests

Sorry, if something is missing. Please make a Pull-Request or open an Issue if something is missing.

# Configuration
To configure your Bot, please make a copy of *default_config.json* and name it *config.json* or change the name in *bot.py* to according to your filename:
> configFile = 'config.json'

## Create a Telegram-Bot
To use the Bot you need Telegram of course.
You have to create a Bot via the *BotFather* described here: https://core.telegram.org/bots#6-botfather
At the end you will receive a api-key which have to be placed in your *config.json*.

## Kanboard-Configuration
You will need a User with a (hopefully) strong password.
To use most of the actions, it needs Administrator-rights.

Please delete the Numbers for *granted_group*, *granted_user*, *granted_user_admin* and *maingroup-id*. They should show you, in which format the IDs have to be placed (as integers ;) ).
I hope they wont collide with existing IDs, so please delete them.
