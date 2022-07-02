#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ssl
import os
# from urllib import request
import requests
from aiohttp import web
import telebot
import json

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
    if answer.headers['Content-Type'] == 'application/json':
        if message.chat.id == message.from_user.id:
            cleaning_group_id = -37549110
            hcwbot.send_message(cleaning_group_id, answer.text)
        else:
            hcwbot.reply_to(message, answer.text)
    elif answer.headers['Content-Type'] == 'image/png':
        hcwbot.send_photo(message.chat.id, answer.content, reply_to_message_id = str(message))

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

"""@langteabot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    url = 'http://localhost:'+os.environ.get('LANGTEABOT_PORT')+'/test'
    content = requests.get(url)
    langteabot.reply_to(message, content.text)
"""
#@langteabot.message_handler(func=lambda message: True, content_types=['text'])
@langteabot.message_handler(commands=['show_prompt'])
def echo_message(message):
    url = 'http://localhost:'+os.environ.get('LANGTEABOT_PORT')+'/show_prompt'
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

@langteabot.message_handler(commands=['set_stop_words'])
def echo_message(message):
    url = 'http://localhost:'+os.environ.get('LANGTEABOT_PORT')+'/set_stop_words'
    data = {
        "user_id": message.from_user.id,
        "stop_words": message.text[len('/set_stop_words '):]
        }
    request_str = json.dumps(data)
    content = requests.post(url, json=request_str)    
    langteabot.reply_to(message, content.text)


# receive audio from telegram
@langteabot.message_handler(func=lambda message: True, content_types=['voice'])
def echo_voice(message):
    
    file_info = langteabot.get_file(message.voice.file_id)
    downloaded_file = langteabot.download_file(file_info.file_path)    
    url = 'http://localhost:'+os.environ.get('LANGTEABOT_PORT')+'/voice'
    # send voice as bytes via post
    #r = requests.post(url, files={'voice': downloaded_file})
    # send user_id + voice as bytes, via post
    r = requests.post(url, files={
        'user_id': message.from_user.id, 
        'voice': downloaded_file
        })

    # response returned as
    # web.FileResponse(filename+'.wav')
    #return as audio message
    langteabot.send_voice(message.chat.id, r.content)
    #langteabot.reply_to(message, 'test')

# === langteabot --

def main():

    app = web.Application()
    app.router.add_post('/{token}/', handle)
    app.router.add_route('GET', '/test', call_test)
    # Build ssl context
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV)

    # Start aiohttp server
    web.run_app(
        app,
        host=WEBHOOK_LISTEN,
        port=os.environ.get('DOCKER_PORT', ''),
        ssl_context=context,
    )


if __name__ == "__main__":
        main()
