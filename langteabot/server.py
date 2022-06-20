from aiohttp import web
#from deeppavlov import build_model
import os
import uuid
import asyncio
import wave
import websockets
import json


def accept_feature_extractor(phrases, accept):
    if len(accept) > 1 and accept['text'] != '':
        accept_text = str(accept['text'])
        conf_score = []
        for result_rec in accept['result']:
            """print(
                '#',
                result_rec['conf'],
                result_rec['start'],
                result_rec['end'],
                result_rec['word']
                )"""
            conf_score.append(float(result_rec['conf']))
        conf_mid = str(sum(conf_score)/len(conf_score))
        print('=== middle confidence:', conf_mid, '\n')
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


async def call_test(request):
        content = "get ok"
        return web.Response(text=content, content_type="text/html")


async def call_voice(request):        
        # get voice file from post request
        reader = await request.multipart()
        field = await reader.next()
        # filename = field.filename
        # generate a random token for the filename
        filename = str(uuid.uuid4())
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
        #user_text = asyncio.run(stt(os.environ.get('STT_SERVER', ''), filename+'.wav'))
        # user_text = stt(os.environ.get('STT_SERVER', ''), filename+'.wav')
        
        #content = filename+'.wav'
        return web.Response(text=user_text, content_type="text/html")


#def main():
app = web.Application(client_max_size=1024**3)
app.router.add_route('GET', '/test', call_test)
app.router.add_route('POST', '/voice', call_voice)
web.run_app(app, port=os.environ.get('PORT', ''))

#if __name__ == "__main__":
#        main()
