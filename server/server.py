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

# init logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

WEBHOOK_HOST = os.environ.get('WEBHOOK_HOST', '')
WEBHOOK_PORT = os.environ.get('WEBHOOK_PORT', '')  # 443, 80, 88 or 8443 (port need to be 'open')
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
        wh_res = bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,certificate=open(WEBHOOK_SSL_CERT, 'r'))
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


bots	= []

# === @id37bot ++

id37bot	= default_bot_init('ID37BOT_TOKEN')
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


# === @executebot ++

executebot	= default_bot_init('EXECUTEBOT_TOKEN')
bots.append(executebot)

@executebot.message_handler(commands=['help', 'start'])
def send_help(message):
    # send message hello
    executebot.reply_to(message, "Hello, I'm ExecuteBot")

@executebot.message_handler(commands=['prompts'])
def prompts_list(message):
    # Keyboard
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    try:
        data_path = 'data/'
        with open(data_path+'prompts.json', 'r') as f:
            prompts = json.load(f)
        for prompt in prompts:
            keyboard.add(telebot.types.KeyboardButton(prompt))
        executebot.send_message(message.chat.id, "Choose your interlocutor", reply_markup=keyboard)
    except Exception as e:
        executebot.reply_to(message, e)

@executebot.message_handler(func=lambda message: True, content_types=['text'])
def send_user(message):
    try:
        data_path = 'data/'
        with open(data_path+'prompts.json', 'r') as f:
            prompts = json.load(f)

        if message.text in prompts:
            # executebot.send_message(message.chat.id, prompts[message.text])
            # Send message and close the buttons
            executebot.send_message(message.chat.id, prompts[message.text], reply_markup=telebot.types.ReplyKeyboardRemove())
        else:
            executebot.reply_to(message, "lambda")
    except Exception as e:
        executebot.reply_to(message, e)

# === @executebot --


# === home_cleaners_watcher_bot ++

hcwbot	= default_bot_init('HCWBOT_TOKEN')
bots.append(hcwbot)

"""@hcwbot.message_handler(commands=['help', 'start'])
def send_help(message):
    link = 'https://service.icecorp.ru/help.mp4'
    hcwbot.send_video(message.chat.id, link, reply_to_message_id = str(message))
"""

@hcwbot.message_handler(func=lambda message: True, content_types=['text'])
def send_user(message):
    url = 'http://localhost:'+os.environ.get('HCWBOT_PORT')+'/message'
    data = {
            "message": message.text,
            "group": message.chat.id,
            "user": message.from_user.id
            }
    request_str = json.dumps(data)
    answer = requests.post(url, json=request_str)
    # there are two types of content_type:
    # application/json
    # image/png
    # Check the content type
    if answer.headers['Content-Type'] == 'image/png':
        hcwbot.send_photo(message.chat.id, answer.content, reply_to_message_id = str(message))
    else: 
        #  answer.headers['Content-Type'] == 'application/json':
        if message.chat.id == message.from_user.id:
            cleaning_group_id = -37549110
            hcwbot.send_message(cleaning_group_id, answer.text)
        else:
            hcwbot.reply_to(message, answer.text)    

# === home_cleaners_watcher_bot --


# === calcubot ++

calcubot	= default_bot_init('CALCUBOT_TOKEN')
bots.append(calcubot)

@calcubot.message_handler(commands=['help', 'start'])
def send_help(message):
    link = 'https://service.icecorp.ru/help.mp4'
    calcubot.send_video(message.chat.id, link, reply_to_message_id = str(message))


@calcubot.message_handler(func=lambda message: True, content_types=['text'])
def send_user(message):
    url = 'http://localhost:'+os.environ.get('CALCUBOT_PORT')+'/message'
    reaction = True
    # check is it group ?
    if message.chat.type == 'group' or message.chat.type == 'supergroup':
        # check, does message contains '/cl ' ?
        if not message.text.startswith('/cl '):
            reaction = False
    if reaction:
        data = {
            "message": message.text,
            "user_id": message.from_user.id,
            "inline": 0
            }
        request_str = json.dumps(data)
        answer = json.loads(requests.post(url, json=request_str).text)
        calcubot.reply_to(message, answer)

@calcubot.inline_handler(func=lambda chosen_inline_result: True)
def query_text(inline_query):
    message_text_prepared = inline_query.query.strip()
    if message_text_prepared!='':
        url = 'http://localhost:'+os.environ.get('CALCUBOT_PORT')+'/message'
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
            telebot.types.InputTextMessageContent( answer[0] ),
            )

        # answer 1        
        r1 = telebot.types.InlineQueryResultArticle(
            '1', 
            answer[1], 
            telebot.types.InputTextMessageContent( answer[1] ),
            )

        # answer 2
        r2 = telebot.types.InlineQueryResultArticle(
            '2', 
            answer[2], 
            telebot.types.InputTextMessageContent( answer[2] ), 
            )

        answer = [r0,r1,r2]

        calcubot.answer_inline_query(
            inline_query.id, 
            answer, 
            cache_time=0, 
            is_personal=True
            ) # updated
    else:
        answer	= ['Empty expression..']
        responce = [
            telebot.types.InlineQueryResultArticle(
                'result', 
                answer[0], 
                telebot.types.InputTextMessageContent( answer[0] )
                )
            ] 
        calcubot.answer_inline_query(inline_query.id, responce)

# === calcubot --


# === langteabot ++

langteabot	= default_bot_init('LANGTEABOT_TOKEN')
bots.append(langteabot)

@langteabot.message_handler(commands=['check_balance'])
def echo_message(message):
    url = 'http://localhost:'+os.environ.get('LANGTEABOT_PORT')+'/check_balance'
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

@langteabot.message_handler(commands=['show_names'])
def echo_message(message):
    url = 'http://localhost:'+os.environ.get('LANGTEABOT_PORT')+'/show_names'
    data = {"user_id": message.from_user.id}
    request_str = json.dumps(data)
    content = requests.post(url, json=request_str)    
    langteabot.reply_to(message, content.text)

@langteabot.message_handler(commands=['reset_prompt'])
def echo_message(message):
    url = 'http://localhost:'+os.environ.get('LANGTEABOT_PORT')+'/reset_prompt'
    data = {"user_id": message.from_user.id}
    request_str = json.dumps(data)
    content = requests.post(url, json=request_str)    
    langteabot.reply_to(message, content.text)

@langteabot.message_handler(commands=['prompts'])
def prompts_list(message):
    # Keyboard
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    try:
        data_path = 'data/'
        with open(data_path+'prompts.json', 'r') as f:
            prompts = json.load(f)
        for prompt in prompts:
            keyboard.add(telebot.types.KeyboardButton(prompt))
        langteabot.send_message(message.chat.id, "Choose your interlocutor", reply_markup=keyboard)
    except Exception as e:
        langteabot.reply_to(message, e)

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

@langteabot.message_handler(commands=['set_names'])
def echo_message(message):
    url = 'http://localhost:'+os.environ.get('LANGTEABOT_PORT')+'/set_names'
    data = {
        "user_id": message.from_user.id,
        "names": message.text[len('/set_names '):]
        }
    request_str = json.dumps(data)
    content = requests.post(url, json=request_str)    
    langteabot.reply_to(message, content.text)

"""@langteabot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    url = 'http://localhost:'+os.environ.get('LANGTEABOT_PORT')+'/regular_message'
    data = {
        "user_id": message.from_user.id,
        "message": message.text
        }
    request_str = json.dumps(data)
    content = requests.post(url, json=request_str)    
    langteabot.reply_to(message, content.text)"""


@langteabot.message_handler(func=lambda message: True, content_types=['text'])
def send_user(message):
    try:
        data_path = 'data/'
        with open(data_path+'prompts.json', 'r') as f:
            prompts = json.load(f)

        if message.text in prompts:            
            if message.text == 'Customizable':
                # Set prompt expectation
                url = 'http://localhost:'+os.environ.get('LANGTEABOT_PORT')+'/set_prompt'
                data = {
                    "user_id": message.from_user.id,
                    "prompt": message.text[len('/set_prompt '):]
                    }
                request_str = json.dumps(data)
                content = requests.post(url, json=request_str)
                # Send message and close the buttons
                langteabot.send_message(message.chat.id, content.text, reply_markup=telebot.types.ReplyKeyboardRemove())
            else:
                # Set selected prompt
                url = 'http://localhost:'+os.environ.get('LANGTEABOT_PORT')+'/set_prompt_selection'
                data = {
                    "user_id": message.from_user.id,
                    "prompt": prompts[message.text]
                    }
                request_str = json.dumps(data)
                content = requests.post(url, json=request_str)
                # Send message and close the buttons
                langteabot.send_message(message.chat.id, content.text, reply_markup=telebot.types.ReplyKeyboardRemove())
                # Send message and close the buttons
                # langteabot.send_message(message.chat.id, prompts[message.text], reply_markup=telebot.types.ReplyKeyboardRemove())
        else:
            # Receive user's prompt
            url = 'http://localhost:'+os.environ.get('LANGTEABOT_PORT')+'/regular_message'
            data = {
                "user_id": message.from_user.id,
                "message": message.text
                }
            request_str = json.dumps(data)
            content = requests.post(url, json=request_str)    
            langteabot.reply_to(message, content.text)
    except Exception as e:
        executebot.reply_to(message, e)

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
