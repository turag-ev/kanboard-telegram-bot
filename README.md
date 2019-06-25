# kanboard-telegram-bot
is a [Telegram-Bot](https://core.telegram.org/bots) with Kanboard and permission features.
It's main purpose is the ability to provide a interface for your [Kanboard](https://github.com/kanboard/) via the [Kanboard-API](https://docs.kanboard.org/en/latest/api/index.html).
While Telegram-Bots are generally open for everyone, the bot provides security/permission features.

Also it's based to be used with groups.
Especially with one main-group which is the verification for the Bots access rights.

The Bot is currently tested with *Python 2.7.15+* and *Kanboard 1.2.9*.

# Usage
Please do the *Installation* and *Configuration* beforehand.

_To be done._

# Installation
I assume, that you're a Telegram-User and have your own Kanboard installed.

Please install the following:

### Telegram-Bot for Python
https://python-telegram-bot.org/

### Kanboard for Python
https://pypi.org/project/kanboard/

### Additional Packages

None.

Sorry, if something is missing.
Please make a Pull-Request or open an Issue if something is missing.

# Configuration
To configure your Bot, please make a copy of *default_config.json* and name it *config.json* or change the name in *bot.py* according to your filename:
> configFile = 'config.json'

Tip: Don't commit your config, if you're forking this repo.

### Create a Telegram-Bot
To use the Bot you need Telegram of course.
You have to create a Bot via the *BotFather* described here: https://core.telegram.org/bots#6-botfather

At the end you will receive a api-key which have to be placed in your *config.json*.

### Kanboard-Configuration
You will need a seperate Bot-User with a (hopefully) strong password.
Most of the actions out of the Kanboard-API need Administrator-rights.
Please add the login-informations and the kanboard-url to your config.
Also create a group in which all your users will be placed, after you/they excecute the command */updategroups* and place the name in your config.
(I personally need this feature, to give access to all Kanboard-Projects with rights to this group).
Cause your config includes the api-key and clearname passwords, I added *config.json* to the gitignore-File. So please don't commit it for your own security!

### Bot-Configuration
Please delete the Numbers for *granted_group*, *granted_user*, *granted_user_admin* and *maingroup-id* in your config. They only should show you, in which format the IDs have to be placed (as integers ;) ).
I hope they wont collide with existing IDs, so please delete them to make your Bot secure.

Cause you deleted the four numbers, nobody has rights to the bot.

Let's check it together:
Start the bot with
> python bot.py

and start the bot in Telegram.
It should show you, that you don't have any access rights.
But the Bot serves you an ID (if nothing happens, try to excecute */help*).
Please copy this ID to your config at *granted_user_admin*.
Restart the Bot and you're the Administrator!

Do the same to your Bot, which is member of your main-group and place the ID (it should have a minus at the beginning) as *maingroup-id*.
Now everything should be setted up.
Execute */reloadconfig* and your Bot should work like described in chapter *Usage*.

# Known Bugs
Kanboard-API doesn't handle Umlaute quite well.

Overall code-structure isn't ideal yet.

Command */addid* has no verification right now. Use it carefully! Duplications of user-IDs could occur.

Help menu has no language-support right now.
