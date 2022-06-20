#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ssl
import os
from urllib import request
import requests
from aiohttp import web
import telebot

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

# f37bot
f37bot	= default_bot_init('F37T1BOT_TOKEN')
bots.append(f37bot)

@f37bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    f37bot.reply_to(message, message.text)

# langteabot
langteabot	= default_bot_init('LANGTEABOT_TOKEN')
bots.append(langteabot)

@langteabot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    url = 'http://localhost:'+os.environ.get('LANGTEABOT_PORT')+'/test'
    content = requests.get(url)
    langteabot.reply_to(message, content.text)

# receive audio from telegram
@langteabot.message_handler(func=lambda message: True, content_types=['voice'])
def echo_voice(message):
    file_info = langteabot.get_file(message.voice.file_id)
    downloaded_file = langteabot.download_file(file_info.file_path)    
    url = 'http://localhost:'+os.environ.get('LANGTEABOT_PORT')+'/voice'
    # send voice as bytes via post
    r = requests.post(url, files={'voice': downloaded_file})

    # files = {'voice': open(message.voice.file_path, 'rb')}
    # requests.post(url, files=files)
    langteabot.reply_to(message, r.text)


def main():

    app = web.Application()
    app.router.add_post('/{token}/', handle)

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
