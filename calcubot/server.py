from urllib import response
from aiohttp import web
import json
import os
import subprocess
from telebot import types

def secure_eval(expression):
    ExpressionOut = subprocess.Popen(
    ['python3', 'calculate.py',expression],
    stdout=subprocess.PIPE, 
    stderr=subprocess.STDOUT)
    stdout,stderr = ExpressionOut.communicate()
    return( stdout.decode("utf-8").replace('\n','') )


async def call_message(request):
    # load data
    data = json.loads(await request.json())
    expression = data['message']
    inline = data['inline']
    answer_max_lenght       = 4095
    res = str(secure_eval(expression))[:answer_max_lenght]
    # prepare response
    if inline=='False':
        response = json.dumps(str(res) + ' = ' + expression)
        return web.Response(text=response, content_type='application/json')
    else:
        answer  = [
                    (str(res) + ' = ' + res),
                    expression + ' = ' + str(res),
                    res
                ]
        # answer 0
        button_names = [str(res)]
        if not answer[0] in button_names:
            button_names.append(answer[0])
        if not expression in button_names:
            button_names.append(expression)
        r0 = types.InlineQueryResultArticle(
            '0', 
            answer[0], 
            types.InputTextMessageContent( answer[0] ),
            #markup_buttons(button_names)
            )

        # answer 1
        button_names = [expression]
        if not answer[1] in button_names:
            button_names.append(answer[1])
        if not str(res) in button_names:
            button_names.append(str(res))
        r1 = types.InlineQueryResultArticle(
            '1', 
            answer[1], 
            types.InputTextMessageContent( answer[1] ),
            #markup_buttons(button_names)
            )

        # answer 2
        r2 = types.InlineQueryResultArticle(
            '2', 
            answer[2], 
            types.InputTextMessageContent( answer[2] ), 
            #markup_buttons([answer[2]])
            )
        response = json.dumps([r0, r1, r2])
        return web.Response(text=response, content_type='application/json')


def main():
    app = web.Application(client_max_size=1024**3)    
    app.router.add_route('POST', '/message', call_message)    
    web.run_app(app, port=os.environ.get('PORT', ''))


if __name__ == "__main__":
    main()
