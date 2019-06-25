#!/usr/bin/env python
# -*- coding: utf-8 -*-

#MIT License

#Copyright (c) 2019 Lukas Müller, Johannes Herold, Florian Völker, TURAG e.V.

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

###############################################################################

import logging
import json
import urllib2
import os
import commands
import copy
from datetime import datetime
from telegram.ext import Updater
from telegram.ext import CommandHandler
from kanboard import Kanboard

configFile = 'config.json'

#####################################

def load_language_json():
    global lang

    try:
        with open(str(languageFile)) as json_data_file:
            lang = json.load(json_data_file)
    except:
        print("Can't open language-file or syntax-error!")
        exit()
    return

def reload_json():
    global data
    global bot_name
    global languageFile
    global kb_url
    global kb_user
    global kb_pw
    global kb_default_project_group
    global bot_token
    global tg_web_prev
    global tg_granted_group
    global tg_granted_user
    global tg_granted_user_admin
    global tg_maingroup_id

    try:
        with open(configFile) as json_data_file:
            data = json.load(json_data_file)
    except:
        print("Can't open config-file or syntax-error!")
        exit()

    bot_name = data["bot"]["name"]
    languageFile = data["bot"]["lang_file"]
    kb_url = data["kb"]["url"]
    kb_user = data["kb"]["user"]
    kb_pw = data["kb"]["passwd"]
    kb_default_project_group = data["kb"]["default_group"]
    bot_token = data["telegram"]["api-key"]
    tg_web_prev = data["telegram"]["disable-web-page-preview"]
    tg_granted_group = data["telegram"]["granted_group"]
    tg_granted_user = data["telegram"]["granted_user"]
    tg_granted_user_admin = data["telegram"]["granted_user_admin"]
    tg_maingroup_id = data["telegram"]["maingroup-id"]

    load_language_json()
    return

#####################################

reload_json()

updater = Updater(token=bot_token)
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

#connect to kanboard
try:
    kb = Kanboard(kb_url , kb_user, kb_pw)
except:
    print(str(lang["error"]["load_bot"]))

#####################################
def has_permission(bot, update):
    access = False
    cur_id = update.message.chat_id

    for g in range(0, len(tg_granted_group)):
        if int(cur_id) == int(tg_granted_group[g]):
            access = True
            return access

    for u in range(0, len(tg_granted_user)):
        if int(cur_id) == int(tg_granted_user[u]):
            access = True
            return access

    for a in range(0, len(tg_granted_user_admin)):
        if int(cur_id) == int(tg_granted_user_admin[a]):
            access = True
            return access

    return access

def is_admin(bot, update):
    access = False
    cur_id = update.message.chat_id

    for a in range(0, len(tg_granted_user_admin)):
        if int(cur_id) == int(tg_granted_user_admin[a]):
            access = True
            return access

    return access

def is_group_member(bot, group_id, user_id):
    is_member = False
    try:
        group_member = bot.getChatMember(chat_id=group_id, user_id=user_id)
        if group_member["status"] == "left":
            is_member = False

        if group_member["status"] == "member" or group_member["status"] == "administrator" or group_member["status"] == "creator":
            is_member = True
    except:
        is_member = False

    return is_member

def sendMessage(bot, update, msg):
    bot.send_message(chat_id=update.message.chat_id, text=str(msg), parse_mode="Markdown")
    return

#####################################
# Functions for commands:
#####################################
#start
def cmd_start(bot, update):
    sendMessage(bot, update, lang["start"]["message"])
    cmd_help(bot, update)

#####################################
#lists
def cmd_lists(bot, update):
    if not has_permission(bot, update):
        sendMessage(bot, update, lang["error"]["user_not_allowed"])
        return

    try:
        projects = kb.get_my_projects()
    except:
        sendMessage(bot, update, lang["error"]["bot_not_kb_allow"])
        return

    if len(projects) == 0:
        sendMessage(bot, update, lang["error"]["cmd_lists_no"])
        return

    msg = lang["cmd"]["cmd_lists"]["lists"] + '\n'

    for k in range(0, len(projects)):
        msg += '*' + 'ID ' + projects[int(k)]["id"] + ':* '+ projects[int(k)]["name"] + '\n'

    sendMessage(bot, update, msg)
    return

#####################################
#list
def cmd_list(bot, update, args = []):
    if not has_permission(bot, update):
        sendMessage(bot, update, lang["error"]["user_not_allowed"])
        return

    if len(args) != 1:
        sendMessage(bot, update, lang["cmd"]["cmd_list"]["usage"])
        return

    list_name = args.pop()
    if list_name == "all":      # reserved keyword to display all todo lists at once with /show all
        sendMessage(bot, update, lang["cmd"]["cmd_list"]["name"] + " " + list_name + " " + lang["cmd"]["cmd_list"]["reserved"])
        return

    try:
        projects = kb.get_my_projects()
    except:
        sendMessage(bot, update, lang["error"]["bot_not_kb_allow"])
        return

    for k in range(0, len(projects)):
        if list_name == projects[int(k)]["name"]:
            sendMessage(bot, update, lang["cmd"]["cmd_list"]["exist"])
            return

    try:
        my_user_id = kb.getMe()["id"]
    except:
        sendMessage(bot, update, lang["error"]["bot_not_kb_allow"])
        return

    try:
        cur_project_id = kb.createProject(name=list_name,owner_id=my_user_id)
        sendMessage(bot, update, lang["cmd"]["cmd_list"]["created"] + " " + list_name)
    except:
        sendMessage(bot, update, lang["error"]["bot_not_kb_allow"])
        return

    try:
        groups = kb.getAllGroups()

        for g in range(0, len(groups)):
            if kb_default_project_group == groups[int(g)]["name"]:
                cur_group_id = groups[int(g)]["id"]
                break
    except:
        sendMessage(bot, update, lang["error"]["bot_not_kb_allow"])
        return

    try:
        kb.addProjectGroup(project_id=cur_project_id, group_id=cur_group_id)
    except:
        sendMessage(bot, update, lang["error"]["bot_not_kb_allow"])
        return

#####################################
#show
def cmd_show(bot, update, args = []):
    if not has_permission(bot, update):
        sendMessage(bot, update, lang["error"]["user_not_allowed"])
        return

    if len(args) != 1:
        sendMessage(bot, update, lang["cmd"]["cmd_show"]["usage"])
        return
    list_name = args.pop()

    try:
        if not list_name == "all":
            projects = kb.get_ProjectByName(name=list_name)
            project_id = projects["id"]
        else:
            sendMessage(bot, update, lang["processing"])
            projects = kb.get_my_projects()
    except:
        sendMessage(bot, update, lang["cmd"]["cmd_show"]["unknown"])
        return

    if len(projects) == 0:
        sendMessage(bot, update, lang["error"]["cmd_list_no"])
        return

    try:
        users = kb.getAllUsers()
    except:
        sendMessage(bot, update, lang["error"]["bot_not_kb_allow"])
        return

    if list_name == "all":
        msg = lang["cmd"]["cmd_show"]["here"] +'\n'

        for k in range(0, len(projects)):
            cur_project_id = projects[int(k)]["id"]
            cur_list_name = projects[int(k)]["name"]
            tasks = kb.get_AllTasks(project_id=cur_project_id, status_id=1) #status_id=1 for active tasks. Otherwise =0

            msg += '*' + cur_list_name + '*\n'
            for t in range(0, len(tasks)):
                cur_owner_id = tasks[int(t)]["owner_id"]

                if int(cur_owner_id) is not 0:
                    for u in range(0, len(users)):
                        if users[int(u)]["id"] == cur_owner_id:
                            msg += '*' + 'ID ' + tasks[int(t)]["id"] + ':* '+ tasks[int(t)]["title"] + ' _(' + users[int(u)]["name"] + ')_' + '\n'
                            break
                else:
                    msg += '*' + 'ID ' + tasks[int(t)]["id"] + ':* '+ tasks[int(t)]["title"] + '\n'
            msg += '\n'
    else:
        msg = '*' + list_name + '*\n'
        tasks = kb.get_AllTasks(project_id=project_id, status_id=1) #status_id=1 for active tasks. Otherwise =0

        for t in range(0, len(tasks)):
            cur_owner_id = tasks[int(t)]["owner_id"]

            if int(cur_owner_id) is not 0:
                for u in range(0, len(users)):
                    if users[int(u)]["id"] == cur_owner_id:
                        msg += '*' + 'ID ' + tasks[int(t)]["id"] + ':* '+ tasks[int(t)]["title"] + ' _(' + users[int(u)]["name"] + ')_' + '\n'
                        break
            else:
                msg += '*' + 'ID ' + tasks[int(t)]["id"] + ':* '+ tasks[int(t)]["title"] + '\n'
        msg += '\n'


    try:
        bot.send_message(chat_id=update.message.chat_id, disable_web_page_preview=tg_web_prev, text=msg, parse_mode="Markdown")
    except:
        bot.send_message(chat_id=update.message.chat_id, text=lang["cmd"]["cmd_show"]["error"])

#####################################
#todo
def cmd_todo(bot, update, args = []):
    if not has_permission(bot, update):
        sendMessage(bot, update, lang["error"]["user_not_allowed"])
        return

    if len(args) < 2:
        sendMessage(bot, update, lang["cmd"]["cmd_todo"]["usage"])
        return

    try:
        project = kb.get_ProjectByName(name=args.pop(0))
    except:
        sendMessage(bot, update, lang["cmd"]["cmd_todo"]["unknown"])
        return

    try:
        task_id = kb.create_task(project_id=project["id"], title=' '.join(args))
        sendMessage(bot, update, lang["done"])
    except:
        sendMessage(bot, update, lang["error"]["bot_not_kb_allow"])

#####################################
#delete
def cmd_delete(bot, update, args = []):
    if not has_permission(bot, update):
        sendMessage(bot, update, lang["error"]["user_not_allowed"])
        return

    if len(args) != 1:
        sendMessage(bot, update, lang["cmd"]["cmd_delete"]["usage"])
        return
    try:
	    project = kb.get_ProjectByName(name=args.pop())
    except:
        sendMessage(bot, update, lang["cmd"]["cmd_delete"]["unknown"])
        return
    try:
        kb.disableProject(project_id=project["id"])
        sendMessage(bot, update, lang["done"])
    except:
        sendMessage(bot, update, lang["error"]["bot_not_kb_allow"])

#####################################
#details
def cmd_details(bot, update, args = []):
    if not has_permission(bot, update):
        sendMessage(bot, update, lang["error"]["user_not_allowed"])
        return

    if len(args) != 1:
        sendMessage(bot, update, lang["cmd"]["cmd_details"]["usage"])
        return
    todo=args.pop()

    sendMessage(bot, update, lang["processing"])

    try:
        users = kb.getAllUsers()
    except:
        sendMessage(bot, update, lang["error"]["bot_not_kb_allow"])
        return

    try:
        task = kb.getTask(task_id=todo)
    except:
        sendMessage(bot, update, lang["cmd"]["cmd_details"]["no_task"])
        return

    try:
        subtasks = kb.getAllSubtasks(task_id=todo)
    except:
        sendMessage(bot, update, lang["cmd"]["cmd_details"]["no_subtask"])
        return

    msg = '*' + lang["cmd"]["cmd_details"]["here"] + " " + task["id"] + '*\n'
    msg += lang["cmd"]["cmd_details"]["title"] + " " + task["title"] + '\n'

    if int(task["is_active"]) is 1:
        status = lang["cmd"]["cmd_details"]["active"]
    else:
        status = lang["cmd"]["cmd_details"]["closed"]

    msg += lang["cmd"]["cmd_details"]["status"] + " " + status + '\n'
    msg += '\n'
    msg += lang["cmd"]["cmd_details"]["description"] + " " + task["description"] + '\n'
    msg += '\n'

    msg += lang["cmd"]["cmd_details"]["subtasks"] + " " + '\n'

    for st in range(0, len(subtasks)):
        if not int(subtasks[int(st)]["status"]) == 2:
            if int(subtasks[int(st)]["user_id"]) is not 0:
                msg += '*' + lang["cmd"]["cmd_details"]["subid"] + " " + subtasks[int(st)]["id"] + ':* '+ subtasks[int(st)]["title"] + ' _(' + subtasks[int(st)]["name"] + ')_' + '\n'
            else:
                msg += '*' + lang["cmd"]["cmd_details"]["subid"] + " " + subtasks[int(st)]["id"] + ':* '+ subtasks[int(st)]["title"] + '\n'

    try:
        project = kb.getProjectById(project_id=int(task["project_id"]))
    except:
        sendMessage(bot, update, lang["error"]["bot_not_kb_allow"])

    msg += '\n'
    msg += lang["cmd"]["cmd_details"]["projid"] + " " + project["name"] + " (" + task["project_id"] + ')\n'

    cur_owner_id = task["owner_id"]

    if int(cur_owner_id) is not 0:
        for u in range(0, len(users)):
            if users[int(u)]["id"] == cur_owner_id:
                msg += lang["cmd"]["cmd_details"]["owner"] + " " + users[int(u)]["name"]  + '\n'
                break
    else:
        msg += lang["cmd"]["cmd_details"]["owner"] + " " + lang["cmd"]["cmd_details"]["none"] + '\n'

    #msg += '*Category-ID:* '+ task["category_id"] + '\n'

    cur_creator_id = task["creator_id"]

    if int(cur_creator_id) is not 0:
        for u in range(0, len(users)):
            if users[int(u)]["id"] == cur_creator_id:
                msg += lang["cmd"]["cmd_details"]["creator"] + " " + users[int(u)]["name"]  + '\n'
                break
    else:
        msg += lang["cmd"]["cmd_details"]["creator"] + " " + lang["cmd"]["cmd_details"]["none"] + '\n'

    msg += lang["cmd"]["cmd_details"]["url"] + ' [' + lang["cmd"]["cmd_details"]["linktext"] + ']('+ task["url"] + ') \n'

    try:
        bot.send_message(chat_id=update.message.chat_id, disable_web_page_preview=tg_web_prev, text=msg, parse_mode="Markdown")
    except:
        sendMessage(bot, update, lang["cmd"]["cmd_details"]["error"])

#####################################
#done
def cmd_done(bot, update, args = []):
    if not has_permission(bot, update):
        sendMessage(bot, update, lang["error"]["user_not_allowed"])
        return

    if len(args) != 1:
        sendMessage(bot, update, lang["cmd"]["cmd_done"]["usage"])
        return
    todo=args.pop()

    try:
        kb.closeTask(task_id=todo)
        task = kb.getTask(task_id=todo)
        sendMessage(bot, update, task["title"] +"\n"+lang["done"])
    except:
        sendMessage(bot, update, lang["cmd"]["cmd_done"]["no_task"])

#####################################
#updateGroups
def cmd_updateGroups(bot, update):
    if not has_permission(bot, update):
        sendMessage(bot, update, lang["error"]["user_not_allowed"])
        return

    reload_json()

    sendMessage(bot, update, lang["processing"])

    try:
        groups = kb.getAllGroups()

        for g in range(0, len(groups)):
            if kb_default_project_group == groups[int(g)]["name"]:
                cur_group_id = groups[int(g)]["id"]
                break
    except:
        sendMessage(bot, update, lang["error"]["bot_not_kb_allow"])
        return

    try:
        users = kb.getAllUsers()
    except:
        sendMessage(bot, update, lang["error"]["bot_not_kb_allow"])
        return

    try:
        for u in range(0, len(users)):
            cur_user_id = users[int(u)]["id"]
            if not kb.isGroupMember(group_id=cur_group_id,user_id=cur_user_id):
                kb.addGroupMember(group_id=cur_group_id,user_id=cur_user_id)
        sendMessage(bot, update, lang["cmd"]["cmd_updateGroups"]["updated"])
    except:
        sendMessage(bot, update, lang["error"]["bot_not_kb_allow"])

#####################################
#test permissions
def cmd_test_permission(bot, update, args = []):
    sendMessage(bot, update, lang["cmd"]["cmd_test_permission"]["test"])
    sendMessage(bot, update, lang["cmd"]["cmd_test_permission"]["id"] + " " + str(update.message.chat_id))

    if has_permission(bot, update):
        sendMessage(bot, update, lang["access_rights"])
    else:
        sendMessage(bot, update, lang["error"]["user_not_allowed"])
    return

#####################################
#cmd_add_id
def cmd_add_id(bot, update, args = []):
    if not is_admin(bot, update):
        sendMessage(bot, update, lang["error"]["user_not_allowed"])
        return


    if len(args) != 2:
        msg = lang["cmd"]["cmd_add_id"]["usage"]
        sendMessage(bot, update, msg)
        return

    cur_type=args.pop(0)
    cur_id=args.pop(0)
    msg = ''

    reload_json()

    if cur_type == "group":
        data["telegram"]["granted_group"].append(int(cur_id))
        msg = lang["cmd"]["cmd_add_id"]["saved"] + " " + str(cur_id) + " " + lang["cmd"]["cmd_add_id"]["to"] + " " + str(cur_type)
    elif cur_type == "user":
        data["telegram"]["granted_user"].append(int(cur_id))
        msg = lang["cmd"]["cmd_add_id"]["saved"] + " " + str(cur_id) + " " + lang["cmd"]["cmd_add_id"]["to"] + " " + str(cur_type)
    elif cur_type == "admin":
        data["telegram"]["granted_user_admin"].append(int(cur_id))
        msg = lang["cmd"]["cmd_add_id"]["saved"] + " " + str(cur_id) + " " + lang["cmd"]["cmd_add_id"]["to"] + " " + str(cur_type)
    else:
        msg = lang["cmd"]["cmd_add_id"]["unknown"] + '\n'
        msg += lang["cmd"]["cmd_add_id"]["usage"] + '\n'
        sendMessage(bot, update, msg)
        return

    try:
        with open(configFile, "w") as write_file:
            json.dump(data, write_file)
    except:
        msg = lang["cmd"]["cmd_add_id"]["error"]

    reload_json()

    sendMessage(bot, update, msg)
    return

#####################################
#cmd_reload_json
def cmd_reload_json(bot, update):
    if not is_admin(bot, update):
        sendMessage(bot, update, lang["error"]["user_not_allowed"])
        return

    reload_json()

    sendMessage(bot, update, lang["done"])
    return

#####################################
#cmd_join
def cmd_join(bot, update):
    if has_permission(bot, update):
        sendMessage(bot, update, lang["access_rights"])
        return

    if update.message.chat_id <= 0:
        sendMessage(bot, update, lang["cmd"]["cmd_join"]["error_group"])
        return

    if not is_group_member(bot, tg_maingroup_id, update.message.chat_id):
        sendMessage(bot, update, lang["cmd"]["cmd_join"]["no_join"])
        return

    reload_json()

    data["telegram"]["granted_user"].append(update.message.chat_id)

    try:
        with open(configFile, "w") as write_file:
            json.dump(data, write_file)
    except:
        sendMessage(bot, update, lang["cmd"]["cmd_join"]["error_write"])
        return

    reload_json()

    sendMessage(bot, update, lang["start"]["welcome"])
    return

#####################################
#cmd_update_rights
def cmd_update_rights(bot, update):
    if not is_admin(bot, update):
        sendMessage(bot, update, lang["error"]["user_not_allowed"])
        return

    reload_json()

    msg=''

    before_tg_granted_user = copy.copy(tg_granted_user)

    for u in range(len(before_tg_granted_user)-1, 0, -1):
        if not is_group_member(bot, tg_maingroup_id, before_tg_granted_user[u]):
            data["telegram"]["granted_user"].pop(u)
            msg += lang["cmd"]["cmd_update_rights"]["delete"] + " " + str(before_tg_granted_user[u]) + '\n'

    try:
        with open(configFile, "w") as write_file:
            json.dump(data, write_file)
        msg += lang["done"]
    except:
        msg = lang["cmd"]["cmd_update_rights"]["error_write"]
        return

    reload_json()

    sendMessage(bot, update, msg)
    return

#####################################
#####################################
#help
def cmd_help(bot, update):
    msg = "*" +str(bot_name) + " Usage:*\n"
    msg += "*/start* - Start the bot.\n"
    msg += "*/lists* - Show all available lists.\n"
    msg += "*/list* _name_ - Create a new list called _name_.\n"
    msg += "*/todo* _list text_ - Create a new todo in _list_.\n"
    msg += "*/show* _list_ - Show todos in _list_.\n"
    msg += "*/show* _all_ - Show all todos.\n"
    msg += "*/done* _id_ - Finish todo _id_.\n"
    msg += "*/details* _id_ - Show details of todo _id_.\n"
    msg += "*/updategroups* - Add users to default-group.\n"
    msg += "*/delete* _list_ - Disable _list_ and all its todos.\n"
    msg += "*/help* - Display this message.\n\n"

    if is_admin(bot, update):
        msg += "*Admin-Features:*\n"
        msg += "*/testpermission* - Test permissions and show ID (Works for everyone).\n"
        msg += "*/addid* _type_ _id_ - Add new Telegram _id_ as _type_\n"
        msg += "               (type could be group, user or admin).\n"
        msg += "*/reloadconfig* - Reload the config. Includes permissions.\n"
        msg += "*/join* - Only usable for new members. Don't add their ID manually again!\n"
        msg += "*/updaterights* - Removes users, which are not in maingroup anymore!\n"

    if not has_permission(bot, update):
        chat_id = update.message.chat_id

        msg = "*" +str(bot_name) + " Usage:*\n"
        msg += "Not allowed for you!\n\n"
        msg += "Your ID is: " + str(chat_id) + "\n"
        msg += "*/help* - Display this message.\n"
        msg += "*/join* - Join if you're worthy.\n"

    sendMessage(bot, update, msg)


start_handler = CommandHandler('start', cmd_start)
lists_handler = CommandHandler('lists', cmd_lists)
list_handler = CommandHandler('list', cmd_list, pass_args=True)     # list is a reserved word in python!
todo_handler = CommandHandler('todo', cmd_todo, pass_args=True)
show_handler = CommandHandler('show', cmd_show, pass_args=True)
delete_handler = CommandHandler('delete', cmd_delete, pass_args=True)
details_handler = CommandHandler('details', cmd_details, pass_args=True)
done_handler = CommandHandler('done', cmd_done, pass_args=True)
update_group_handler = CommandHandler('updategroups', cmd_updateGroups)
help_handler = CommandHandler('help', cmd_help)
test_permission_handler = CommandHandler('testpermission', cmd_test_permission, pass_args=True)
add_id_handler = CommandHandler('addid', cmd_add_id, pass_args=True)
reload_json_handler = CommandHandler('reloadconfig', cmd_reload_json)
join_handler = CommandHandler('join', cmd_join)
update_rights_handler = CommandHandler("updaterights" ,cmd_update_rights)


dispatcher.add_handler(start_handler)
dispatcher.add_handler(lists_handler)
dispatcher.add_handler(list_handler)
dispatcher.add_handler(todo_handler)
dispatcher.add_handler(show_handler)
dispatcher.add_handler(delete_handler)
dispatcher.add_handler(details_handler)
dispatcher.add_handler(done_handler)
dispatcher.add_handler(update_group_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(test_permission_handler)
dispatcher.add_handler(add_id_handler)
dispatcher.add_handler(reload_json_handler)
dispatcher.add_handler(join_handler)
dispatcher.add_handler(update_rights_handler)

updater.start_polling()
raw_input("Press any key to exit...")
updater.stop()
exit()
