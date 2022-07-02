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


def accept_feature_extractor(phrases, accept):
    if len(accept) > 1 and accept['text'] != '':
        accept_text = str(accept['text'])
        conf_score = []
        for result_rec in accept['result']:
            conf_score.append(float(result_rec['conf']))
        conf_mid = str(sum(conf_score)/len(conf_score))
        phrases.append(accept_text)


async def stt(uri, file_name):

    async with websockets.connect(uri) as websocket:

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

        return ' '.join(phrases)


def tts(tts_text, filename):
    tts_server = os.environ.get('TTS_SERVER', '')
    data={'text': tts_text}
    request_str = json.dumps(data)
    response = requests.post(tts_server+'/inference', json=request_str)
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
    # read prompt from user config
    config = read_config(user_id)
    config['last_cmd'] = 'show_prompt'
    save_config(config, user_id)
    content = 'Stop words:'+str(config['stop_words'])+'\n'+config['prompt']
    return web.Response(text=content, content_type="text/html")


async def call_reset_prompt(request):
    request_str = json.loads(str(await request.text()))
    data = json.loads(request_str)
    user_id = str(data['user_id'])
    # read default prompt
    config = load_default_config(user_id)
    config['last_cmd'] = 'reset_prompt'
    save_config(config, user_id)    
    return web.Response(text='Prompt reset successfull', content_type="text/html")


async def call_set_prompt(request):
    request_str = json.loads(str(await request.text()))
    data = json.loads(request_str)
    user_id = str(data['user_id'])
    # read prompt from user config
    config = read_config(user_id)
    # set new prompt
    # config['prompt'] = data['prompt']
    config['last_cmd'] = 'set_prompt'
    save_config(config, user_id)    
    return web.Response(text='Please, send a new prompt', content_type="text/html")


async def call_set_stop_words(request):
    request_str = json.loads(str(await request.text()))
    data = json.loads(request_str)
    user_id = str(data['user_id'])
    # read prompt from user config
    config = read_config(user_id)
    # set new stop_words
    config['stop_words'] = data['stop_words']
    config['last_cmd'] = 'set_stop_words'
    save_config(config, user_id)
    return web.Response(text='Stop words set successfull', content_type="text/html")


async def call_regular_message(request):
    request_str = json.loads(str(await request.text()))
    data = json.loads(request_str)
    user_id = str(data['user_id'])
    # read prompt from user config
    config = read_config(user_id)

    answer = 'Regular messsage received'

    if config['last_cmd'] == 'set_prompt':
        config['prompt'] = data['message']
        answer = 'Prompt set successfull'

    config['last_cmd'] = 'regular_message'
    save_config(config, user_id)
    return web.Response(text=answer, content_type="text/html")


async def call_voice(request):
    # get user_id and voice file from post request
    reader = await request.multipart()
    
    # read user_id
    field = await reader.next()        
    user_id = await field.read()
    # convert bytearray to text
    user_id = user_id.decode('utf-8')

    # Read accepted users list from text file
    granted_users = []
    with open('granted_users.txt', 'r') as f:
        for line in f:
            granted_users.append(line.strip())

    # generate a random token for the filename
    filename = str(uuid.uuid4())
    # Check is user id in accepted users
    if user_id in granted_users:
        
        # read voice file
        field = await reader.next()        
        voice = await field.read()
        # save voice file
        with open(filename+'.ogg', 'wb') as new_file:
            new_file.write(voice)
            
        # convert to wav
        os.system('ffmpeg -i '+filename+'.ogg -ac 1 -ar 16000 '+filename+'.wav -y')
        # remove ogg file
        os.remove(filename+'.ogg')
        # transcribe and receive response
        user_text = await stt(os.environ.get('STT_SERVER', ''), filename+'.wav')        

        config = read_config(user_id)

        # safe
        if len(config['prompt']) > 1500:
            config = load_default_config(user_id)

        # openai conversation
        # init
        stop_words = config['stop_words']        
        prompt = config['prompt']    
        #prompt_len = len(prompt.split('\n'))
        prompt += '\n'+stop_words[0]+' ' + user_text + '\n'+stop_words[1]+' '
        bot_text = text_davinci(str(prompt), stop_words)['choices'][0]['text']
        prompt += bot_text.replace('\n', '')

        # update prompt in user config
        config['prompt'] = prompt
        save_config(config, user_id)

        # append datetime and prompt to logs/prompt_[iser_id].csv
        # splitter is ;
        with open('logs/prompt_'+user_id+'.csv', 'a') as f:
            f.write(str(dt.now())+';'+prompt+'\n')

        # remove wav file
        os.remove(filename+'.wav')
    else:
        bot_text = 'You are not allowed to use this service, sorry'

    # synthesis text to speech
    tts(bot_text, filename)

    # read audio file
    with open(filename+'.wav', 'rb') as f:
        content = f.read()
    # remove wav file
    os.remove(filename+'.wav')
    # append content and bot_text to response
    return web.Response(body=content, content_type="audio/wav")


def main():
    app = web.Application(client_max_size=1024**3)    
    app.router.add_route('POST', '/voice', call_voice)
    app.router.add_route('POST', '/show_prompt', call_show_prompt)
    app.router.add_route('POST', '/reset_prompt', call_reset_prompt)
    app.router.add_route('POST', '/set_prompt', call_set_prompt)
    app.router.add_route('POST', '/set_stop_words', call_set_stop_words)
    app.router.add_route('POST', '/regular_message', call_regular_message)
    web.run_app(app, port=os.environ.get('PORT', ''))


if __name__ == "__main__":
    main()
