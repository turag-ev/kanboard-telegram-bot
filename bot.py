#!/usr/bin/env python3
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
import requests			# simple http requests
import os
import copy
from datetime import datetime
from telegram.ext import Updater
from telegram.ext import CommandHandler
import kanboard
import random

configFile = 'config.json'

#####################################

ignore = 'robots.txt'

#####################################

def load_language_json():
    global lang

    try:
        with open(str(languageFile)) as json_data_file:
            lang = json.load(json_data_file)
    except Exception as e:
        print("Can't open language-file or syntax-error!")
        print(e)
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

def getMultilineStr(lines):
    return "\n".join(lines)

#####################################

reload_json()

updater = Updater(token=bot_token, use_context=True)
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

#connect to kanboard
try:
    kb = kanboard.Client(kb_url , kb_user, kb_pw)
except:
    print(str(lang["error"]["load_bot"]))

#####################################
def is_granted(cur_id, cur_list):
    for e in range(0, len(cur_list)):
        if int(cur_id) == int(cur_list[e]):
            return True
    return False

def has_permission(update, context):
    access = False
    cur_id = update.message.chat_id

    if is_granted(cur_id, tg_granted_group):
        access = True
        return access

    if is_granted(cur_id, tg_granted_user):
        access = True
        return access

    if is_granted(cur_id, tg_granted_user_admin):
        access = True
        return access

    return access

def is_admin(update, context):
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

def sendMessage(update, context, msg):
    context.bot.send_message(chat_id=update.message.chat_id, text=str(msg), parse_mode="Markdown")
    return

#####################################
# Functions for commands:
#####################################
#start
def cmd_start(update ,context):
    sendMessage(update, context, lang["start"]["message"])
    cmd_help(update, context)

#####################################
#lists
def cmd_lists(update, context):
    if not has_permission(update, context):
        sendMessage(update, context, lang["error"]["user_not_allowed"])
        return

    try:
        projects = kb.get_my_projects()
    except:
        sendMessage(update, context, lang["error"]["bot_not_kb_allow"])
        return

    if len(projects) == 0:
        sendMessage(update, context, lang["error"]["cmd_lists_no"])
        return

    msg = lang["cmd"]["cmd_lists"]["lists"] + '\n'

    for k in range(0, len(projects)):
        cur_description = projects[int(k)]["description"]
        if ignore != cur_description:
            msg += '*' + 'ID ' + projects[int(k)]["id"] + ':* '+ projects[int(k)]["name"] + ' *(' + projects[int(k)]["identifier"] + ')*\n'

    sendMessage(update, context, msg)
    return

#####################################
#list
def cmd_list(update, context):
    args = context.args
    if not has_permission(update, context):
        sendMessage(update, context, lang["error"]["user_not_allowed"])
        return

    if len(args) < 2:
        sendMessage(update, context, lang["cmd"]["cmd_list"]["usage"])
        return

    identifier_name = args.pop(0)
    list_name = ' '.join(args)
    if identifier_name == "all":      # reserved keyword to display all todo lists at once with /show all
        sendMessage(update, context, lang["cmd"]["cmd_list"]["name"] + " " + identifier_name + " " + lang["cmd"]["cmd_list"]["reserved"])
        return

    try:
        projects = kb.get_my_projects()
    except:
        sendMessage(update, context, lang["error"]["bot_not_kb_allow"])
        return

    for k in range(0, len(projects)):
        if identifier_name.upper() == projects[int(k)]["identifier"]:
            sendMessage(update, context, lang["cmd"]["cmd_list"]["exist"])
            return

    try:
        my_user_id = kb.getMe()["id"]
    except:
        sendMessage(update, context, lang["error"]["bot_not_kb_allow"])
        return

    try:
        cur_project_id = kb.createProject(name=list_name,identifier=identifier_name,owner_id=my_user_id)
        sendMessage(update, context, lang["cmd"]["cmd_list"]["created"] + " " + list_name + ' (' + identifier_name +')')
    except:
        sendMessage(update, context, lang["error"]["bot_not_kb_allow"])
        return

    try:
        groups = kb.getAllGroups()

        for g in range(0, len(groups)):
            if kb_default_project_group == groups[int(g)]["name"]:
                cur_group_id = groups[int(g)]["id"]
                break
    except:
        sendMessage(update, context, lang["error"]["bot_not_kb_allow"])
        return

    try:
        kb.addProjectGroup(project_id=cur_project_id, group_id=cur_group_id)
    except:
        sendMessage(update, context, lang["error"]["bot_not_kb_allow"])
        return

#####################################
#show
def cmd_show(update, context):
    args = context.args
    if not has_permission(update, context):
        sendMessage(update, context, lang["error"]["user_not_allowed"])
        return

    if len(args) != 1:
        sendMessage(update, context, lang["cmd"]["cmd_show"]["usage"])
        return
    list_name = args.pop()

    try:
        if not list_name == "all":
            projects = kb.get_ProjectByIdentifier(identifier=list_name)
            project_id = projects["id"]
            project_name = projects["name"]
            project_identifier = projects["identifier"]
        else:
            sendMessage(update, context, lang["processing"])
            projects = kb.get_my_projects()
    except:
        sendMessage(update, context, lang["cmd"]["cmd_show"]["unknown"])
        return

    if len(projects) == 0:
        sendMessage(update, context, lang["error"]["cmd_list_no"])
        return

    try:
        users = kb.getAllUsers()
    except:
        sendMessage(update, context, lang["error"]["bot_not_kb_allow"])
        return

    if list_name == "all":
        msg = lang["cmd"]["cmd_show"]["here"] +'\n'

        for k in range(0, len(projects)):
            cur_project_id = projects[int(k)]["id"]
            cur_list_name = projects[int(k)]["name"]
            cur_project_identifier = projects[int(k)]["identifier"]
            cur_description = projects[int(k)]["description"]
            tasks = kb.get_AllTasks(project_id=cur_project_id, status_id=1) #status_id=1 for active tasks. Otherwise =0

            if ignore != cur_description:
                msg += '*' + cur_list_name + ' (' + cur_project_identifier + ')*\n'
                for t in range(0, len(tasks)):
                    cur_owner_id = tasks[int(t)]["owner_id"]

                    if int(cur_owner_id) != 0:
                        for u in range(0, len(users)):
                            if users[int(u)]["id"] == cur_owner_id:
                                msg += '*' + 'ID ' + tasks[int(t)]["id"] + ':* '+ tasks[int(t)]["title"] + ' _(' + users[int(u)]["name"] + ')_' + '\n'
                                break
                    else:
                        msg += '*' + 'ID ' + tasks[int(t)]["id"] + ':* '+ tasks[int(t)]["title"] + '\n'
                msg += '\n'
    else:
        msg = '*' + project_name + ' (' + project_identifier + ')*\n'
        tasks = kb.get_AllTasks(project_id=project_id, status_id=1) #status_id=1 for active tasks. Otherwise =0

        for t in range(0, len(tasks)):
            cur_owner_id = tasks[int(t)]["owner_id"]

            if int(cur_owner_id) != 0:
                for u in range(0, len(users)):
                    if users[int(u)]["id"] == cur_owner_id:
                        msg += '*' + 'ID ' + tasks[int(t)]["id"] + ':* '+ tasks[int(t)]["title"] + ' _(' + users[int(u)]["name"] + ')_' + '\n'
                        break
            else:
                msg += '*' + 'ID ' + tasks[int(t)]["id"] + ':* '+ tasks[int(t)]["title"] + '\n'
        msg += '\n'


    try:
        context.bot.send_message(chat_id=update.message.chat_id, disable_web_page_preview=tg_web_prev, text=msg, parse_mode="Markdown")
    except:
        context.bot.send_message(chat_id=update.message.chat_id, text=lang["cmd"]["cmd_show"]["error"])

#####################################
#todo
def cmd_todo(update, context):
    args = context.args
    if not has_permission(update, context):
        sendMessage(update, context, lang["error"]["user_not_allowed"])
        return

    if len(args) < 2:
        sendMessage(update, context, lang["cmd"]["cmd_todo"]["usage"])
        return

    try:
        project = kb.get_ProjectByIdentifier(identifier=args.pop(0))
    except:
        sendMessage(update, context, lang["cmd"]["cmd_todo"]["unknown"])
        return

    try:
        task_id = kb.create_task(project_id=project["id"], title=' '.join(args))
        msg = lang["done"] + " ID: " + str(task_id)
        sendMessage(update, context, msg)
    except:
        sendMessage(update, context, lang["error"]["bot_not_kb_allow"])

#####################################
#subtask
def cmd_subtask(update, context):
    args = context.args
    if not has_permission(update, context):
        sendMessage(update, context, lang["error"]["user_not_allowed"])
        return

    if len(args) < 2:
        sendMessage(update, context, lang["cmd"]["cmd_subtask"]["usage"])
        return

    try:
        task_id = kb.get_Task(task_id=args.pop(0))["id"]
    except:
        sendMessage(update, context, lang["cmd"]["cmd_subtask"]["unknown"])
        return

    try:
        subtask_id = kb.create_subtask(task_id=task_id, title=' '.join(args))
        msg = lang["done"] + " Sub-ID: " + str(subtask_id)
        sendMessage(update, context, msg)
    except:
        sendMessage(update, context, lang["error"]["bot_not_kb_allow"])

#####################################
#delete
def cmd_delete(update, context):
    args = context.args
    if not has_permission(update, context):
        sendMessage(update, context, lang["error"]["user_not_allowed"])
        return

    if len(args) != 1:
        sendMessage(update, context, lang["cmd"]["cmd_delete"]["usage"])
        return
    try:
	    project = kb.get_ProjectByIdentifier(identifier=args.pop())
    except:
        sendMessage(update, context, lang["cmd"]["cmd_delete"]["unknown"])
        return
    try:
        kb.disableProject(project_id=project["id"])
        sendMessage(update, context, lang["done"])
    except:
        sendMessage(update, context, lang["error"]["bot_not_kb_allow"])

#####################################
#details
def cmd_details(update, context):
    args = context.args
    if not has_permission(update, context):
        sendMessage(update, context, lang["error"]["user_not_allowed"])
        return

    if len(args) != 1:
        sendMessage(update, context, lang["cmd"]["cmd_details"]["usage"])
        return
    todo=args.pop()

    sendMessage(update, context, lang["processing"])

    try:
        users = kb.getAllUsers()
    except:
        sendMessage(update, context, lang["error"]["bot_not_kb_allow"])
        return

    try:
        task = kb.getTask(task_id=todo)
    except:
        sendMessage(update, context, lang["cmd"]["cmd_details"]["no_task"])
        return

    try:
        subtasks = kb.getAllSubtasks(task_id=todo)
    except:
        sendMessage(update, context, lang["cmd"]["cmd_details"]["no_subtask"])
        return

    msg = '*' + lang["cmd"]["cmd_details"]["here"] + " " + task["id"] + '*\n'
    msg += lang["cmd"]["cmd_details"]["title"] + " " + task["title"] + '\n'

    if int(task["is_active"]) == 1:
        status = lang["cmd"]["cmd_details"]["active"]
    else:
        status = lang["cmd"]["cmd_details"]["closed"]

    msg += lang["cmd"]["cmd_details"]["status"] + " " + status + '\n'
    msg += '\n'
    msg += lang["cmd"]["cmd_details"]["description"] + '\n'

    if task["description"] is not None:
        msg += task["description"] + '\n'

    msg += '\n'

    msg += lang["cmd"]["cmd_details"]["subtasks"] + " " + '\n'

    for st in range(0, len(subtasks)):
        status_id = int(subtasks[int(st)]["status"])

        if status_id == 1:
            status_id_msg = " " + lang["cmd"]["cmd_details"]["wip"]
        else:
            status_id_msg = ""

        if status_id != 2:
            if int(subtasks[int(st)]["user_id"]) != 0:
                msg += '*' + lang["cmd"]["cmd_details"]["subid"] + " " + subtasks[int(st)]["id"] + ':*' + status_id_msg + ' ' + subtasks[int(st)]["title"] + ' _(' + subtasks[int(st)]["name"] + ')_' + '\n'
            else:
                msg += '*' + lang["cmd"]["cmd_details"]["subid"] + " " + subtasks[int(st)]["id"] + ':*' + status_id_msg + ' ' + subtasks[int(st)]["title"] + '\n'

    try:
        project = kb.getProjectById(project_id=int(task["project_id"]))
    except:
        sendMessage(update, context, lang["error"]["bot_not_kb_allow"])

    msg += '\n'
    msg += lang["cmd"]["cmd_details"]["projid"] + " " + project["name"] + " (" + task["project_id"] + ')\n'

    cur_owner_id = task["owner_id"]

    if int(cur_owner_id) != 0:
        for u in range(0, len(users)):
            if users[int(u)]["id"] == cur_owner_id:
                msg += lang["cmd"]["cmd_details"]["owner"] + " " + users[int(u)]["name"]  + '\n'
                break
    else:
        msg += lang["cmd"]["cmd_details"]["owner"] + " " + lang["cmd"]["cmd_details"]["none"] + '\n'

    #msg += '*Category-ID:* '+ task["category_id"] + '\n'

    cur_creator_id = task["creator_id"]

    if int(cur_creator_id) != 0:
        for u in range(0, len(users)):
            if users[int(u)]["id"] == cur_creator_id:
                msg += lang["cmd"]["cmd_details"]["creator"] + " " + users[int(u)]["name"]  + '\n'
                break
    else:
        msg += lang["cmd"]["cmd_details"]["creator"] + " " + lang["cmd"]["cmd_details"]["none"] + '\n'

    msg += lang["cmd"]["cmd_details"]["url"] + ' [' + lang["cmd"]["cmd_details"]["linktext"] + ']('+ task["url"] + ') \n'

    try:
        context.bot.send_message(chat_id=update.message.chat_id, disable_web_page_preview=tg_web_prev, text=msg, parse_mode="Markdown")
    except:
        sendMessage(update, context, lang["cmd"]["cmd_details"]["error"])

#####################################
#done
def cmd_done(update, context):
    args = context.args
    if not has_permission(update, context):
        sendMessage(update, context, lang["error"]["user_not_allowed"])
        return

    if len(args) != 1:
        sendMessage(update, context, lang["cmd"]["cmd_done"]["usage"])
        return
    todo=args.pop()

    try:
        kb.closeTask(task_id=todo)
        task = kb.getTask(task_id=todo)
        sendMessage(update, context, task["title"] +"\n"+lang["done"])
    except:
        sendMessage(update, context, lang["cmd"]["cmd_done"]["no_task"])

#####################################
#undone
def cmd_undone(update, context):
    args = context.args
    if not has_permission(update, context):
        sendMessage(update, context, lang["error"]["user_not_allowed"])
        return

    if len(args) != 1:
        sendMessage(update, context, lang["cmd"]["cmd_undone"]["usage"])
        return
    todo=args.pop()

    try:
        kb.openTask(task_id=todo)
        task = kb.getTask(task_id=todo)
        sendMessage(update, context, task["title"] +"\n"+lang["undone"])
    except:
        sendMessage(update, context, lang["cmd"]["cmd_undone"]["no_task"])

#####################################
#cmd_activity
def cmd_activity(update, context):
    args = context.args
    if not has_permission(update, context):
        sendMessage(update, context, lang["error"]["user_not_allowed"])
        return

    if len(args) != 1:
        sendMessage(update, context, lang["cmd"]["cmd_activity"]["usage"])
        return
    list_name = args.pop()

    sendMessage(update, context, lang["processing"])

    try:
        if not list_name == "all":
            projects = kb.get_ProjectByIdentifier(identifier=list_name)
            activities = kb.get_ProjectActivity(project_id=projects["id"])
        else:
            projects = kb.get_my_projects()

            ids = []
            for k in range(0, len(projects)):
                cur_project_id = projects[int(k)]["id"]
                ids.append(cur_project_id)

            activities = kb.get_ProjectActivities(project_ids=ids)
    except:
        sendMessage(update, context, lang["cmd"]["cmd_activity"]["unknown"])
        return

    msg = lang["cmd"]["cmd_activity"]["here"] +'\n'
    out = 0

    for k in range(0, len(activities)):
        if activities[int(k)]["event_name"] in ["subtask.create","subtask.close","task.create","task.close"]:

            if activities[int(k)]["event_name"] in ["subtask.create","subtask.close"]:
                title = activities[int(k)]["subtask"]["title"]
            else:
                title = activities[int(k)]["task"]["title"]

            msg += '*' + activities[int(k)]["task"]["project_name"] + ':* ' + activities[int(k)]["event_title"] + ' (' + title + ') \n\n'
            out = out + 1

            if out > 30:
                break

        #print (activities[int(k)]["event_name"])
        #print(activities[int(k)])
        #print("##########################")

    sendMessage(update, context, msg)

#####################################
#updateGroups
def cmd_updateGroups(update, context):
    if not has_permission(update, context):
        sendMessage(update, context, lang["error"]["user_not_allowed"])
        return

    reload_json()

    sendMessage(update, context, lang["processing"])

    try:
        groups = kb.getAllGroups()

        for g in range(0, len(groups)):
            if kb_default_project_group == groups[int(g)]["name"]:
                cur_group_id = groups[int(g)]["id"]
                break
    except:
        sendMessage(update, context, lang["error"]["bot_not_kb_allow"])
        return

    try:
        users = kb.getAllUsers()
    except:
        sendMessage(update, context, lang["error"]["bot_not_kb_allow"])
        return

    try:
        for u in range(0, len(users)):
            cur_user_id = users[int(u)]["id"]
            if not kb.isGroupMember(group_id=cur_group_id,user_id=cur_user_id):
                kb.addGroupMember(group_id=cur_group_id,user_id=cur_user_id)
        sendMessage(update, context, lang["cmd"]["cmd_updateGroups"]["updated"])
    except:
        sendMessage(update, context, lang["error"]["bot_not_kb_allow"])

#####################################
#test permissions
def cmd_test_permission(update, context):
    args = context.args
    sendMessage(update, context, lang["cmd"]["cmd_test_permission"]["test"])
    sendMessage(update, context, lang["cmd"]["cmd_test_permission"]["id"] + " " + str(update.message.chat_id))

    if has_permission(update, context):
        sendMessage(update, context, lang["access_rights"])
    else:
        sendMessage(update, context, lang["error"]["user_not_allowed"])
    return

#####################################
#cmd_add_id
def cmd_add_id(update, context):
    args = context.args
    if not is_admin(update, context):
        sendMessage(update, context, lang["error"]["user_not_allowed"])
        return


    if len(args) != 2:
        msg = lang["cmd"]["cmd_add_id"]["usage"]
        sendMessage(update, context, msg)
        return

    cur_type=args.pop(0)
    cur_id=args.pop(0)
    msg = ''
    existing = True

    reload_json()

    if cur_type == "group":
        if not is_granted(cur_id, tg_granted_group):
            data["telegram"]["granted_group"].append(int(cur_id))
            msg = lang["cmd"]["cmd_add_id"]["saved"] + " " + str(cur_id) + " " + lang["cmd"]["cmd_add_id"]["to"] + " " + str(cur_type)
            existing = False
    elif cur_type == "user":
        if not is_granted(cur_id, tg_granted_user):
            data["telegram"]["granted_user"].append(int(cur_id))
            msg = lang["cmd"]["cmd_add_id"]["saved"] + " " + str(cur_id) + " " + lang["cmd"]["cmd_add_id"]["to"] + " " + str(cur_type)
            existing = False
    elif cur_type == "admin":
        if not is_granted(cur_id, tg_granted_user_admin):
            data["telegram"]["granted_user_admin"].append(int(cur_id))
            msg = lang["cmd"]["cmd_add_id"]["saved"] + " " + str(cur_id) + " " + lang["cmd"]["cmd_add_id"]["to"] + " " + str(cur_type)
            existing = False
    else:
        msg = lang["cmd"]["cmd_add_id"]["unknown"] + '\n'
        msg += lang["cmd"]["cmd_add_id"]["usage"] + '\n'
        sendMessage(update, context, msg)
        return

    if not existing:
        try:
            with open(configFile, "w") as write_file:
                json.dump(data, write_file)
        except:
            msg = lang["cmd"]["cmd_add_id"]["error"]
    else:
        msg = lang["cmd"]["cmd_add_id"]["existing"]

    reload_json()

    sendMessage(update, context, msg)
    return

#####################################
#cmd_show_id
def cmd_show_id(update, context):
    args = context.args
    if not is_admin(update, context):
        sendMessage(update, context, lang["error"]["user_not_allowed"])
        return

    reload_json()

    msg = "*Maingroup:*" + "\n"
    msg += str(tg_maingroup_id) + "\n"

    msg += "\n*Groups:*" + "\n"
    for g in range(0, len(tg_granted_group)):
        msg += str(tg_granted_group[g]) + "\n"

    msg += "\n*Admins:*" + "\n"
    for g in range(0, len(tg_granted_user_admin)):
        msg += str(tg_granted_user_admin[g]) + "\n"

    msg += "\n*Users:*" + "\n"
    for g in range(0, len(tg_granted_user)):
        msg += str(tg_granted_user[g]) + "\n"

    sendMessage(update, context, msg)
    return

#####################################
#cmd_reload_json
def cmd_reload_json(update, context):
    args = context.args
    if not is_admin(update, context):
        sendMessage(update, context, lang["error"]["user_not_allowed"])
        return

    reload_json()

    sendMessage(update, context, lang["done"])
    return

#####################################
#cmd_join
def cmd_join(update, context):
    if has_permission(update, context):
        sendMessage(update, context, lang["access_rights"])
        return

    if update.message.chat_id <= 0:
        sendMessage(update, context, lang["cmd"]["cmd_join"]["error_group"])
        return

    if not is_group_member(context.bot, tg_maingroup_id, update.message.chat_id):
        sendMessage(update, context, lang["cmd"]["cmd_join"]["no_join"])
        return

    reload_json()

    data["telegram"]["granted_user"].append(update.message.chat_id)

    try:
        with open(configFile, "w") as write_file:
            json.dump(data, write_file)
    except:
        sendMessage(update, context, lang["cmd"]["cmd_join"]["error_write"])
        return

    reload_json()

    sendMessage(update, context, lang["start"]["welcome"])
    return

#####################################
#cmd_update_rights
def cmd_update_rights(update, context):
    if not is_admin(update, context):
        sendMessage(update, context, lang["error"]["user_not_allowed"])
        return

    reload_json()

    msg=''

    before_tg_granted_user = copy.copy(tg_granted_user)

    for u in range(len(before_tg_granted_user)-1, 0, -1):
        if not is_group_member(context.bot, tg_maingroup_id, before_tg_granted_user[u]):
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

    sendMessage(update, context, msg)
    return

#####################################
#####################################
#help
def cmd_help(update, context):
    if has_permission(update, context):
        # General commands
        msg = getMultilineStr(lang["cmd"]["cmd_help"]["general"]).format(bot_name)
        msg += "\n\n"

        if is_admin(update, context):
            # Admin commands
            msg += getMultilineStr(lang["cmd"]["cmd_help"]["admin"])
    else:
        # No permission
        chat_id = update.message.chat_id
        msg = getMultilineStr(lang["cmd"]["cmd_help"]["no_permission"]).format(bot_name, chat_id)

    sendMessage(update, context, msg)


start_handler = CommandHandler('start', cmd_start)
lists_handler = CommandHandler('lists', cmd_lists)
list_handler = CommandHandler('list', cmd_list, pass_args=True)     # list is a reserved word in python!
todo_handler = CommandHandler('todo', cmd_todo, pass_args=True)
subtask_handler = CommandHandler('subtask', cmd_subtask, pass_args=True)
show_handler = CommandHandler('show', cmd_show, pass_args=True)
delete_handler = CommandHandler('delete', cmd_delete, pass_args=True)
details_handler = CommandHandler('details', cmd_details, pass_args=True)
done_handler = CommandHandler('done', cmd_done, pass_args=True)
undone_handler = CommandHandler('undone', cmd_undone, pass_args=True)
update_group_handler = CommandHandler('updategroups', cmd_updateGroups)
help_handler = CommandHandler('help', cmd_help)
test_permission_handler = CommandHandler('testpermission', cmd_test_permission, pass_args=True)
add_id_handler = CommandHandler('addid', cmd_add_id, pass_args=True)
show_id_handler = CommandHandler('showid', cmd_show_id)
reload_json_handler = CommandHandler('reloadconfig', cmd_reload_json)
join_handler = CommandHandler('join', cmd_join)
update_rights_handler = CommandHandler("updaterights" ,cmd_update_rights)


dispatcher.add_handler(start_handler)
dispatcher.add_handler(lists_handler)
dispatcher.add_handler(list_handler)
dispatcher.add_handler(todo_handler)
dispatcher.add_handler(subtask_handler)
dispatcher.add_handler(show_handler)
dispatcher.add_handler(delete_handler)
dispatcher.add_handler(details_handler)
dispatcher.add_handler(done_handler)
dispatcher.add_handler(undone_handler)
dispatcher.add_handler(update_group_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(test_permission_handler)
dispatcher.add_handler(add_id_handler)
dispatcher.add_handler(show_id_handler)
dispatcher.add_handler(reload_json_handler)
dispatcher.add_handler(join_handler)
dispatcher.add_handler(update_rights_handler)

updater.start_polling()
input("Press any key to exit...")
updater.stop()
exit()
