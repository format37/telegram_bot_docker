#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ssl
import os
# from urllib import request
import requests
from aiohttp import web
import telebot
import json
import logging
import pandas as pd
from datetime import datetime as dt
import re
import pickle
import csv

# init logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

WEBHOOK_HOST = os.environ.get('WEBHOOK_HOST', '')
# 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_PORT = os.environ.get('WEBHOOK_PORT', '')
WEBHOOK_LISTEN = '0.0.0.0'  # In some VPS you may need to put here the IP addr
WEBHOOK_SSL_CERT = 'webhook_cert.pem'
WEBHOOK_SSL_PRIV = 'webhook_pkey.pem'

# Quick'n'dirty SSL certificate generation:
#
# openssl genrsa -out webhook_pkey.pem 2048
# openssl req -new -x509 -days 3650 -key webhook_pkey.pem -out webhook_cert.pem
#
# When asked for "Common Name (e.g. server FQDN or YOUR name)" you should reply
# with the same value in you put in WEBHOOK_HOST

"""logger.info('reading calcubot blocked users')
df = pd.read_csv('calcubot_blocked/users.csv')
df = pd.DataFrame(df.user)
df['user'] = df.user.astype(int)
df = df.sort_values(by=['user'])
calcubot_blocked_users = set(df['user'])
logger.info('Loaded '+str(len(calcubot_blocked_users)) +
            ' calcubot blocked users')
"""
calcubot_unsecure_words = [
        'exec',
        'import',
        'sys',
        'subprocess',
        'eval',
        'open',
        'file',
        'write',
        'read',
        'print',
        'compile'
        'globals',
        'locals',
        'builtins',
        'getattr'
    ]

async def call_test(request):
    logging.info('call_test')
    content = "get ok"
    return web.Response(text=content, content_type="text/html")


def default_bot_init(bot_token_env):
    API_TOKEN = os.environ.get(bot_token_env, '')
    bot = telebot.TeleBot(API_TOKEN)

    WEBHOOK_URL_BASE = "https://{}:{}".format(
        os.environ.get('WEBHOOK_HOST', ''),
        os.environ.get('WEBHOOK_PORT', '')
    )
    WEBHOOK_URL_PATH = "/{}/".format(API_TOKEN)

    # Remove webhook, it fails sometimes the set if there is a previous webhook
    bot.remove_webhook()

    # Set webhook
    wh_res = bot.set_webhook(
        url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH, certificate=open(WEBHOOK_SSL_CERT, 'r'))
    print(bot_token_env, 'webhook set', wh_res)
    # print(WEBHOOK_URL_BASE + WEBHOOK_URL_PATH)

    return bot


# Process webhook calls
async def handle(request):
    for bot in bots:
        if request.match_info.get('token') == bot.token:
            request_body_dict = await request.json()
            update = telebot.types.Update.de_json(request_body_dict)
            bot.process_new_updates([update])
            return web.Response()

    return web.Response(status=403)


bots = []


# === @id37bot ++

id37bot = default_bot_init('ID37BOT_TOKEN')
bots.append(id37bot)


@id37bot.message_handler(commands=['user'])
def send_help(message):
    message.from_user.id
    id37bot.reply_to(message, message.from_user.id)


@id37bot.message_handler(commands=['group'])
def send_help(message):
    message.from_user.id
    id37bot.reply_to(message, message.chat.id)

# === @id37bot --


# === @gptaidbot ++
gptaidbot = default_bot_init('GPTAIDBOT_TOKEN')
bots.append(gptaidbot)


@gptaidbot.message_handler(commands=['help', 'start'])
def send_start(message):
    url = 'http://localhost:' + \
        os.environ.get('GPTAIDBOT_PORT')+'/start'
    data = {"user_id": message.from_user.id}
    request_str = json.dumps(data)
    content = requests.post(url, json=request_str)
    gptaidbot.reply_to(message, ""+str(content.json()['result']))


@gptaidbot.inline_handler(func=lambda chosen_inline_result: True)
def query_text(inline_query):
    logger.info("@gptaidbot inline query: {}".format(inline_query.query))
    url = 'http://localhost:' + \
        os.environ.get('GPTAIDBOT_PORT')+'/inline'
    data = {
        "user_id": inline_query.from_user.id,
        "query": inline_query.query
        }
    request_str = json.dumps(data)
    content = requests.post(url, json=request_str)
    
    # answer 0
    r0 = telebot.types.InlineQueryResultArticle(
        '0',
        content.json()['result'],
        telebot.types.InputTextMessageContent(content.json()['result']),
    )
    answer = [r0]

    gptaidbot.answer_inline_query(
        inline_query.id,
        answer,
        cache_time=0,
        is_personal=True
    )
    # logger.info('@gptaidbot answer_inline_query: '+str(answer))
# === @gptaidbot --


# === calcubot ++

calcubot = default_bot_init('CALCUBOT_TOKEN')
bots.append(calcubot)


def read_blocked_csv(filename='calcubot_blocked/blocked.csv'):
    blocked_numbers = []
    if not os.path.exists(filename):
        # logger.info(f"{filename} does not exist.")
        pass
    else:
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                blocked_numbers.append(int(row[0]))

    return blocked_numbers


def add_to_blocked_csv(number, filename='calcubot_blocked/blocked.csv'):
    logger.info('add_to_blocked_csv')
    blocked_numbers = read_blocked_csv(filename)
    if number in blocked_numbers:
        logger.info(f"{number} is already in {filename}.")
        return
    
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([number])
    
    logger.info(f"Added {number} to blocked.csv")

def calcubot_sequrity(request, user_id):
    # Check is request sequre:
    for word in calcubot_unsecure_words:
        if word in request:
            add_to_blocked_csv(user_id)
            return False
    return True


def granted_user(user_id):    
    calcubot_blocked_users = read_blocked_csv()
    user_id = int(user_id)
    if user_id in calcubot_blocked_users:
        logger.info('Blocked user: {}'.format(user_id))
        return False
    else:
        # logger.info('Granted user: {}'.format(user_id))
        return True


def collect_logs():
    try:
        # read all files in logs/
        path = 'calcubot_logs/'
        files = os.listdir(path)

        # create a list of dataframes
        dfs = []
        for file in files:
            with open(path + '/' + file, 'r') as f:
                # read file to a list of strings
                lines = f.readlines()
                user = file[:-4]
                text = ''
                # create a list of lists
                for line in lines:
                    # check, is line starts from re like: 2022-10-27 13:33:43.906742;
                    if re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d{6};', line):
                        if len(text) > 0:
                            record = [[user, date, text]]
                            df = pd.DataFrame(
                                record, columns=['user', 'date', 'request'])
                            dfs.append(df)
                        first_semicolon = line.find(';')
                        left = line[:first_semicolon]
                        date = dt.strptime(left, '%Y-%m-%d %H:%M:%S.%f')
                        # print(date)
                        text = line[first_semicolon + 1:]
                    else:
                        text += line
                if len(text) > 0:
                    record = [[user, date, text]]
                    df = pd.DataFrame(
                        record, columns=['user', 'date', 'request'])
                    dfs.append(df)

        # concat all dfs to a single one
        df = pd.concat(dfs)
        df.to_csv('requests.csv')
        return 'requests.csv'
    except Exception as e:
        logger.error(e)
        return 'error'


@calcubot.message_handler(commands=['help', 'start'])
def send_help(message):
    if granted_user(message.from_user.id):
        link = 'https://service.icecorp.ru/help.mp4'
        calcubot.send_video(message.chat.id, link,
                            reply_to_message_id=str(message))


@calcubot.message_handler(func=lambda message: True, content_types=['text'])
def send_user(message):
    if granted_user(message.from_user.id):
        url = 'http://localhost:'+os.environ.get('CALCUBOT_PORT')+'/message'
        reaction = True
        # check is it group ?
        if message.chat.type == 'group' or message.chat.type == 'supergroup':
            # check, does message contains '/cl ' ?
            if not message.text.startswith('/cl '):
                reaction = False

        if message.from_user.id == 106129214 and message.text.startswith('/logs'):
            file = collect_logs()
            if file == 'error':
                calcubot.reply_to(message, 'error')
            else:
                calcubot.send_document(message.chat.id, open(file, 'rb'))
                reaction = False

        if reaction:
            reaction = calcubot_sequrity(message.text, message.from_user.id)
            if not reaction:
                calcubot.reply_to(message, 'You are blocked')

        if reaction:
            try:
                # append datetime and expression to calcubot_logs/[user_id].csv
                # splitter is ;
                with open('calcubot_logs/'+str(message.from_user.id)+'.csv', 'a') as f:
                    f.write(str(dt.now())+';'+str(message.text)+'\n')
            except Exception as e:
                logger.error(e)
                
            data = {
                "message": message.text,
                "user_id": message.from_user.id,
                "inline": 0
            }
            request_str = json.dumps(data)
            answer = json.loads(requests.post(url, json=request_str).text)
            calcubot.reply_to(message, answer)
    else:
        calcubot.reply_to(message, 'Service unavailable')


@calcubot.inline_handler(func=lambda chosen_inline_result: True)
def query_text(inline_query):
    if granted_user(inline_query.from_user.id) and calcubot_sequrity(inline_query.query, inline_query.from_user.id):

        message_text_prepared = inline_query.query.strip()
        if message_text_prepared != '':
            url = 'http://localhost:' + \
                os.environ.get('CALCUBOT_PORT')+'/message'
            data = {
                "message": inline_query.query,
                "inline": 1
            }
            request_str = json.dumps(data)
            answer = json.loads(requests.post(url, json=request_str).text)

            # answer 0
            r0 = telebot.types.InlineQueryResultArticle(
                '0',
                answer[0],
                telebot.types.InputTextMessageContent(answer[0]),
            )

            # answer 1
            r1 = telebot.types.InlineQueryResultArticle(
                '1',
                answer[1],
                telebot.types.InputTextMessageContent(answer[1]),
            )

            # answer 2
            r2 = telebot.types.InlineQueryResultArticle(
                '2',
                answer[2],
                telebot.types.InputTextMessageContent(answer[2]),
            )

            answer = [r0, r1, r2]

            calcubot.answer_inline_query(
                inline_query.id,
                answer,
                cache_time=0,
                is_personal=True
            )  # updated
        else:
            answer = ['Empty expression..']
            responce = [
                telebot.types.InlineQueryResultArticle(
                    'result',
                    answer[0],
                    telebot.types.InputTextMessageContent(answer[0])
                )
            ]
            calcubot.answer_inline_query(inline_query.id, responce)
    else:
        answer = ['Service unavailable']
        responce = [
            telebot.types.InlineQueryResultArticle(
                'result',
                answer[0],
                telebot.types.InputTextMessageContent(answer[0])
            )
        ]
        calcubot.answer_inline_query(inline_query.id, responce)

# === calcubot --


# === langteabot ++
langteabot = default_bot_init('LANGTEABOT_TOKEN')
bots.append(langteabot)


@langteabot.message_handler(commands=['check_balance'])
def echo_message(message):
    url = 'http://localhost:' + \
        os.environ.get('LANGTEABOT_PORT')+'/check_balance'
    data = {"user_id": message.from_user.id}
    request_str = json.dumps(data)
    content = requests.post(url, json=request_str)
    langteabot.reply_to(message, content.text)


@langteabot.message_handler(commands=['show_prompt'])
def echo_message(message):
    url = 'http://localhost:'+os.environ.get('LANGTEABOT_PORT')+'/show_prompt'
    data = {"user_id": message.from_user.id}
    request_str = json.dumps(data)
    content = requests.post(url, json=request_str)
    langteabot.reply_to(message, content.text)


@langteabot.message_handler(commands=['reset'])
def echo_message(message):
    url = 'http://localhost:'+os.environ.get('LANGTEABOT_PORT')+'/reset_prompt'
    data = {"user_id": message.from_user.id}
    request_str = json.dumps(data)
    content = requests.post(url, json=request_str)
    langteabot.reply_to(message, content.text)


@langteabot.message_handler(commands=['set_prompt'])
def echo_message(message):
    url = 'http://localhost:'+os.environ.get('LANGTEABOT_PORT')+'/set_prompt'
    data = {
        "user_id": message.from_user.id,
        "prompt": message.text[len('/set_prompt '):]
    }
    request_str = json.dumps(data)
    content = requests.post(url, json=request_str)
    langteabot.reply_to(message, content.text)


@langteabot.message_handler(commands=['last_message'])
def last_message(message):
    url = 'http://localhost:'+os.environ.get('LANGTEABOT_PORT')+'/last_message'
    data = {"user_id": message.from_user.id}
    request_str = json.dumps(data)
    content = requests.post(url, json=request_str)
    langteabot.reply_to(message, content.text)


@langteabot.message_handler(commands=['choose_language'])
def languages_list(message):
    # Keyboard
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    try:
        data_path = 'data/'
        with open(data_path+'languages.json', 'r') as f:
            languages = json.load(f)
        for language in languages.values():
            logging.info(str(language))
            keyboard.add(telebot.types.KeyboardButton(language['name']))
        langteabot.send_message(message.chat.id, "Choose the voice language", reply_markup=keyboard)
        # Update the user last cmd
        url = 'http://localhost:' + os.environ.get('LANGTEABOT_PORT') + '/update_settings'
        data = {
            "user_id": message.from_user.id,
            "config": {'last_cmd': 'choose_language'}
        }
        request_str = json.dumps(data)
        r = requests.post(url, json=request_str)
        logger.info(r.text)
    except Exception as e:
        langteabot.reply_to(message, e)


@langteabot.message_handler(func=lambda message: True, content_types=['text'])
def send_user(message):
    try:
        # Receive user's prompt
        url = 'http://localhost:' + \
            os.environ.get('LANGTEABOT_PORT')+'/regular_message'
        data = {
            "user_id": message.from_user.id,
            "message": message.text
        }
        request_str = json.dumps(data)
        content = requests.post(url, json=request_str)
        # Send message and close the buttons
        langteabot.reply_to(message, content.text, reply_markup=telebot.types.ReplyKeyboardRemove())
    except Exception as e:
        langteabot.reply_to(message, e)


# receive audio from telegram
@langteabot.message_handler(func=lambda message: True, content_types=['voice'])
def echo_voice(message):

    file_info = langteabot.get_file(message.voice.file_id)
    downloaded_file = langteabot.download_file(file_info.file_path)
    url = 'http://localhost:'+os.environ.get('LANGTEABOT_PORT')+'/voice'
    # send user_id + voice as bytes, via post
    r = requests.post(url, files={
        'user_id': message.from_user.id,
        'voice': downloaded_file
    })

    # response returned as
    # web.FileResponse(filename+'.wav')
    # return as audio message
    langteabot.send_voice(message.chat.id, r.content)
# === langteabot --


def main():
    logging.info('Init')
    app = web.Application()
    app.router.add_post('/{token}/', handle)
    app.router.add_route('GET', '/test', call_test)
    # Build ssl context
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV)
    logging.info('Starting')
    # Start aiohttp server
    web.run_app(
        app,
        host=WEBHOOK_LISTEN,
        port=os.environ.get('DOCKER_PORT', ''),
        ssl_context=context,
    )


if __name__ == "__main__":
    main()
