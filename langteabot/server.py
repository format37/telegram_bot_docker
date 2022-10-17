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
    """async with websockets.connect(uri) as websocket:

        phrases = []

        wf = wave.open(file_name, "rb")
        await websocket.send(
            '{ "config" : { "sample_rate" : %d } }' % (wf.getframerate())
            )
        buffer_size = int(wf.getframerate() * 0.2)  # 0.2 seconds of audio
        while True:
            data = wf.readframes(buffer_size)

            if len(data) == 0:
                break

            await websocket.send(data)
            accept = json.loads(await websocket.recv())
            accept_feature_extractor(phrases, accept)

        await websocket.send('{"eof" : 1}')
        accept = json.loads(await websocket.recv())
        accept_feature_extractor(phrases, accept)

        return ' '.join(phrases)"""


def tts(tts_text, filename):
    tts_server = os.environ.get('TTS_SERVER', '')
    # data={'text': tts_text}
    # request_str = json.dumps(data)
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


def text_davinci(prompt, stop_words):
    openai.api_key = os.getenv("PHRASE_SEED")
    return json.loads(str(openai.Completion.create(
      engine="text-davinci-002",
      prompt=prompt,
      temperature=0.9,
      max_tokens=150,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0.6,
      stop=stop_words
    )))


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
    content = str(config['prompt'])
    return web.Response(text=content, content_type="text/html")


async def call_show_names(request):
    request_str = json.loads(str(await request.text()))
    data = json.loads(request_str)
    user_id = str(data['user_id'])
    logging.info(str(dt.now())+' '+'User: '+str(user_id)+' call_show_names')
    # read prompt from user config
    config = read_config(user_id)
    config['last_cmd'] = 'show_names'
    save_config(config, user_id)
    content = str(config['names'])
    return web.Response(text=content, content_type="text/html")


def reset_prompt(user_id):
    logging.info(str(dt.now())+' '+'User: '+str(user_id)+' reset_prompt')
    # read default prompt
    config = read_config(user_id)
    init_prompt = config['init_prompt']
    total_tokens = config['total_tokens']
    names = config['names']
    config = load_default_config(user_id)
    config['total_tokens'] = total_tokens
    config['prompt'] = init_prompt
    config['init_prompt'] = init_prompt
    config['names'] = names
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
    return web.Response(text='Please, send a new prompt', content_type="text/html")


async def call_set_names(request):
    request_str = json.loads(str(await request.text()))
    data = json.loads(request_str)
    user_id = str(data['user_id'])
    logging.info(str(dt.now())+' '+'User: '+str(user_id)+' call_set_names')
    # read prompt from user config
    config = read_config(user_id)
    # set new names
    config['last_cmd'] = 'set_names'
    save_config(config, user_id)
    return web.Response(text='Please, tell me Your name', content_type="text/html")


async def call_regular_message(request):
    request_str = json.loads(str(await request.text()))
    data = json.loads(request_str)
    user_id = str(data['user_id'])
    logging.info(str(dt.now())+' '+'User: '+str(user_id)+' call_regular_message')
    # read prompt from user config
    config = read_config(user_id)
        
    answer = 'Regular messsage received'

    if config['last_cmd'] == 'set_prompt':
        config['prompt'] = data['message']
        config['init_prompt'] = data['message']
        config['last_cmd'] = 'regular_message'
        answer = 'Prompt set successfull'        

    elif config['last_cmd'] == 'set_names':
        # save a new stop word to 0th place of config['names']
        # config['names'].insert(0, data['message'])
        config['names'][0] = data['message']
        config['last_cmd'] = 'names_0'
        answer = 'Your name set successfull. Please, send the name of Bot'        

    elif config['last_cmd'] == 'names_0':
        config['names'][1] = data['message']
        config['last_cmd'] = 'names_1'
        answer = "Bot's name set successfull."

    else:
        config['last_cmd'] = 'regular_message'
    
    save_config(config, user_id)
    return web.Response(text=answer, content_type="text/html")


async def call_set_prompt_selection(request):
    request_str = json.loads(str(await request.text()))
    data = json.loads(request_str)
    user_id = str(data['user_id'])
    logging.info(str(dt.now())+' '+'User: '+str(user_id)+' call_set_prompt_selection')
    # read prompt from user config
    config = read_config(user_id)
    new_prompt = data['prompt'].replace('Alex', config['names'][0])
    new_prompt = new_prompt.replace('Jane', config['names'][1])
    config['prompt'] = new_prompt
    config['init_prompt'] = new_prompt
    config['last_cmd'] = 'regular_message'
    answer = new_prompt
    
    save_config(config, user_id)
    return web.Response(text=answer, content_type="text/html")


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

        # openai conversation
        logging.info(str(dt.now())+' '+'User: '+str(user_id)+' call_voice.openai conversation')
        # init
        names = config['names']        
        prompt = config['prompt']    
        #prompt_len = len(prompt.split('\n'))
        prompt += '\n'+names[0]+': ' + user_text + '\n'+names[1]+': '
        davinchi_response = text_davinci(str(prompt), names)
        bot_text = davinchi_response['choices'][0]['text']
        total_tokens = davinchi_response['usage']['total_tokens']
        prompt += bot_text.replace('\n', '')

        # update total_tokens in user config
        config['total_tokens'] = int(config['total_tokens'])+int(total_tokens)

        # update prompt in user config
        config['prompt'] = prompt

        # save config
        save_config(config, user_id)

        # append datetime and prompt to logs/prompt_[iser_id].csv
        # splitter is ;
        with open('logs/prompt_'+user_id+'.csv', 'a') as f:
            f.write(str(dt.now())+';'+prompt+';'+str(total_tokens)+'\n')

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
    app.router.add_route('POST', '/show_names', call_show_names)
    app.router.add_route('POST', '/reset_prompt', call_reset_prompt)
    app.router.add_route('POST', '/set_prompt', call_set_prompt)
    app.router.add_route('POST', '/set_prompt_selection', call_set_prompt_selection)
    app.router.add_route('POST', '/set_names', call_set_names)
    app.router.add_route('POST', '/regular_message', call_regular_message)
    app.router.add_route('POST', '/check_balance', call_check_balance)
    web.run_app(app, port=os.environ.get('PORT', ''))


if __name__ == "__main__":
    main()
