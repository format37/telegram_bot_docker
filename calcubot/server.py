from urllib import response
from aiohttp import web
import json
import os
import subprocess
from telebot import types

def secure_eval(expression, mode):
    ExpressionOut = subprocess.Popen(
    ['python3', 'calculate_'+mode+'.py',expression],
    stdout=subprocess.PIPE, 
    stderr=subprocess.STDOUT)
    stdout,stderr = ExpressionOut.communicate()
    return( stdout.decode("utf-8").replace('\n','') )


async def call_message(request):
    # load data
    data = json.loads(await request.json())
    expression = data['message']
    # if expression contains '/cl ', remove it
    if expression.startswith('/cl '):
        expression = expression[4:]
    inline = int(data['inline'])
    answer_max_lenght = 4095
    # prepare response
    if inline == 0:
        res = str(secure_eval(expression, 'native'))[:answer_max_lenght]
        response = json.dumps(res + ' = ' + expression)
        return web.Response(text=response, content_type='application/json')
    else:
        res = str(secure_eval(expression, 'inline'))[:answer_max_lenght]
        answer  = [
                    res + ' = ' + expression,
                    expression + ' = ' + res,
                    res
                ]
        response = json.dumps(answer)
        return web.Response(text=response, content_type='application/json')


def main():
    app = web.Application(client_max_size=1024**3)    
    app.router.add_route('POST', '/message', call_message)    
    web.run_app(app, port=os.environ.get('PORT', ''))


if __name__ == "__main__":
    main()
