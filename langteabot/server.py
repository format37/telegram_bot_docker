from asyncio.log import logger
from aiohttp import web
import os
import uuid
import asyncio
import wave
import websockets
import json
import openai
import requests
from datetime import datetime as dt
import logging

# enable logging
logging.basicConfig(level=logging.INFO)

def accept_feature_extractor(phrases, accept):
    if len(accept) > 1 and accept['text'] != '':
        accept_text = str(accept['text'])
        conf_score = []
        for result_rec in accept['result']:
            conf_score.append(float(result_rec['conf']))
        conf_mid = str(sum(conf_score)/len(conf_score))
        phrases.append(accept_text)


async def stt(uri, file_name):
    with open(file_name, 'rb') as f:
        r = requests.post(uri, files={'file': f})
    logger.info('stt: '+r.text)
    return r.text


def tts(tts_text, filename):
    tts_server = os.environ.get('TTS_SERVER', '')
    # https://cloud.google.com/text-to-speech/docs/voices
    # https://cloud.google.com/text-to-speech
    logger.info('tts: '+tts_text)
    data = {
        'text':tts_text,
        'language':'en-US',
        'model':'en-US-Neural2-F',
        'speed':1
    }
    response = requests.post(tts_server+'/inference', json=data)
    # Save response as audio file
    with open(filename+".wav", "wb") as f:
        f.write(response.content)


def text_chat_gpt(prompt):
    openai.api_key = os.getenv("PHRASE_SEED")
    answer = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=prompt
    )
    return answer


def load_default_config(user_id):
    conf_path = 'user_conf/'
    with open(conf_path+'config.json', 'r') as f:
        config = json.load(f)
    
    return config


def read_config(user_id):
    conf_path = 'user_conf/'
    # if user.json conf not in user_conf folder, create it
    # default config file: config.json
    if not os.path.exists(conf_path+user_id+'.json'):
        config = load_default_config(user_id)
    else:
        with open(conf_path+user_id+'.json', 'r') as f:
            config = json.load(f)
    return config


def save_config(config, user_id):
    # user configuration
    conf_path = 'user_conf/'
    # save config
    with open(conf_path+user_id+'.json', 'w') as f:
        json.dump(config, f)


async def call_show_prompt(request):
    request_str = json.loads(str(await request.text()))
    data = json.loads(request_str)
    user_id = str(data['user_id'])
    logging.info(str(dt.now())+' '+'User: '+str(user_id)+' call_show_prompt')
    # read prompt from user config
    config = read_config(user_id)
    config['last_cmd'] = 'show_prompt'
    save_config(config, user_id)
    # content = str(config['prompt'])
    content = str(config['chat_gpt_prompt'][-1]['content'])
    return web.Response(text=content, content_type="text/html")


def reset_prompt(user_id):
    logging.info(str(dt.now())+' '+'User: '+str(user_id)+' reset_prompt')
    # read default prompt
    config = read_config(user_id)
    # init_prompt = config['init_prompt']
    chat_gpt_init_prompt = config['chat_gpt_init_prompt']
    total_tokens = config['total_tokens']
    # names = config['names']
    config = load_default_config(user_id)
    config['total_tokens'] = total_tokens
    # config['prompt'] = init_prompt
    # config['init_prompt'] = init_prompt
    config['chat_gpt_prompt'] = chat_gpt_init_prompt
    config['chat_gpt_init_prompt'] = chat_gpt_init_prompt
    # config['names'] = names
    config['last_cmd'] = 'reset_prompt'
    save_config(config, user_id)


async def call_reset_prompt(request):
    request_str = json.loads(str(await request.text()))
    data = json.loads(request_str)
    user_id = str(data['user_id'])
    reset_prompt(user_id)
    return web.Response(text='Prompt reset successfull', content_type="text/html")


async def call_set_prompt(request):
    request_str = json.loads(str(await request.text()))
    data = json.loads(request_str)
    user_id = str(data['user_id'])
    logging.info(str(dt.now())+' '+'User: '+str(user_id)+' call_set_prompt')
    # read prompt from user config
    config = read_config(user_id)
    # set new prompt
    # config['prompt'] = data['prompt']
    config['last_cmd'] = 'set_prompt'
    save_config(config, user_id)
    return web.Response(text='Please, send me a new init prompt', content_type="text/html")


async def call_regular_message(request):
    request_str = json.loads(str(await request.text()))
    data = json.loads(request_str)
    user_id = str(data['user_id'])
    logging.info(str(dt.now())+' '+'User: '+str(user_id)+' call_regular_message')
    # read prompt from user config
    config = read_config(user_id)
        
    answer = 'Regular messsage received'

    if config['last_cmd'] == 'set_prompt':
        config['chat_gpt_prompt'][0]['content'] = data['message']
        config['last_cmd'] = 'regular_message'
        answer = 'Prompt set successfull'
    else:
        config['last_cmd'] = 'regular_message'
        if int(config['total_tokens']) < 0:
            answer = openai_conversation(config, user_id, data['message'])
        else:
            answer = 'Not enough funds. Please, refill your account'
    
    save_config(config, user_id)
    return web.Response(text=answer, content_type="text/html")


async def openai_conversation(config, user_id, user_text):
    # openai conversation
        logging.info(str(dt.now())+' '+'User: '+str(user_id)+' call_voice.openai conversation')
        # init
        chat_gpt_prompt = config['chat_gpt_prompt']
        chat_gpt_prompt.append({"role": "user", "content": str(user_text)})
        openai_response = text_chat_gpt(chat_gpt_prompt)
        bot_text = openai_response['choices'][0]['message']['content']
        chat_gpt_prompt.append({"role": "assistant", "content": bot_text})
        config['chat_gpt_prompt'] = chat_gpt_prompt
        total_tokens = openai_response['usage']['total_tokens']
        config['total_tokens'] = int(config['total_tokens'])+int(total_tokens)

        # save config
        save_config(config, user_id)

        # append datetime and prompt to logs/prompt_[iser_id].csv
        # splitter is ;
        with open('logs/prompt_'+user_id+'.csv', 'a') as f:
            f.write(str(dt.now())+';'+str(chat_gpt_prompt)+';'+str(total_tokens)+'\n')

        return bot_text


async def call_voice(request):
    # get user_id and voice file from post request
    reader = await request.multipart()
    
    # read user_id
    field = await reader.next()        
    user_id = await field.read()
    logging.info(str(dt.now())+' '+'User: '+str(user_id)+' call_voice')
    # convert bytearray to text
    user_id = user_id.decode('utf-8')

    config = read_config(user_id)    

    # Read accepted users list from text file
    #granted_users = []
    #with open('granted_users.txt', 'r') as f:
    #    for line in f:
    #        granted_users.append(line.strip())

    
    # Check is user id in accepted users
    # if user_id in granted_users:

    # check user balance
    if int(config['total_tokens']) < 0:

        # generate a random token for the filename
        filename = str(uuid.uuid4())
        
        # read voice file
        field = await reader.next()        
        voice = await field.read()
        # save voice file
        logging.info(str(dt.now())+' '+'User: '+str(user_id)+' call_voice.save voice file')
        with open(filename+'.ogg', 'wb') as new_file:
            new_file.write(voice)
        logging.info(str(dt.now())+' '+'User: '+str(user_id)+' call_voice.convert to wav')
        # convert to wav
        # os.system('ffmpeg -i '+filename+'.ogg -ac 1 -ar 16000 '+filename+'.wav -y')
        
        # transcribe and receive response
        logging.info(str(dt.now())+' '+'User: '+str(user_id)+' call_voice.transcribe and receive response')
        stt_url = os.environ.get('STT_SERVER', '')+'/inference'
        # user_text = await stt(stt_uri+'/inference', filename+'.wav')
        # with open(file_path, 'rb') as f:
        #     r = requests.post(stt_url, files={'file': f})
        r = requests.post(stt_url, files={'file': voice})
        user_text = r.text

        # remove ogg file
        os.remove(filename+'.ogg')

        # safe
        #if len(config['prompt']) > 1500:
        #    #config = load_default_config(user_id)
        #    reset_prompt(user_id)

        bot_text = openai_conversation(config, user_id, user_text)

        # remove user's voice wav file
        # os.remove(filename+'.wav')

        # synthesis text to speech
        logging.info(str(dt.now())+' '+'User: '+str(user_id)+' call_voice.synthesis text to speech')
        tts(bot_text, filename)
        file_should_be_removed = True
    else:
        filename = 'data/add_funds'
        file_should_be_removed = False

    # read audio file
    with open(filename+'.wav', 'rb') as f:
        content = f.read()

    if file_should_be_removed:
        # remove synthesis wav file
        os.remove(filename+'.wav')
    logging.info(str(dt.now())+' '+'User: '+str(user_id)+' call_voice.response')
    return web.Response(body=content, content_type="audio/wav")


async def call_check_balance(request):
    request_str = json.loads(str(await request.text()))
    data = json.loads(request_str)
    user_id = str(data['user_id'])
    logging.info(str(dt.now())+' '+'User: '+str(user_id)+' call_check_balance')
    # read prompt from user config
    config = read_config(user_id)
    total_tokens = int(config['total_tokens'])
    price = float(config['price'])
    balance = -total_tokens/1000*price
    # round
    balance = round(balance, 2)
    content = '$'+str(balance)+'\nTo top up your balance, just send a message to @format37'
    return web.Response(text=content, content_type="text/html")


def main():
    app = web.Application(client_max_size=1024**3)    
    app.router.add_route('POST', '/voice', call_voice)
    app.router.add_route('POST', '/show_prompt', call_show_prompt)
    app.router.add_route('POST', '/reset_prompt', call_reset_prompt)
    app.router.add_route('POST', '/set_prompt', call_set_prompt)
    app.router.add_route('POST', '/regular_message', call_regular_message)
    app.router.add_route('POST', '/check_balance', call_check_balance)
    web.run_app(app, port=os.environ.get('PORT', ''))


if __name__ == "__main__":
    main()
