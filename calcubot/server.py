from aiohttp import web
import json
import os
import subprocess
from user_defined import *
import pandas as pd
import numpy as np
import scipy
from scipy import stats
import random
import datetime
import statistics
import ast
import math

def secure_eval(expression):
    ExpressionOut = subprocess.Popen(
    ['python3', 'calculate.py',expression],
    stdout=subprocess.PIPE, 
    stderr=subprocess.STDOUT)
    stdout,stderr = ExpressionOut.communicate()
    return( stdout.decode("utf-8").replace('\n','') )


async def call_message(request):
    data = json.loads(await request.json())
    expression = data['message']
    res = str(secure_eval(expression))
    return web.Response(text=res)


def main():
    app = web.Application(client_max_size=1024**3)    
    app.router.add_route('POST', '/message', call_message)    
    web.run_app(app, port=os.environ.get('PORT', ''))


if __name__ == "__main__":
    main()
