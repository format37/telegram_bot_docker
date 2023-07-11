import os
import time
from flask import Flask, request, jsonify, Response
import logging
import json
import openai
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = Flask(__name__)

@app.route("/test")
def call_test():
    return "get ok"


def text_chat_gpt(prompt, model):
    openai.api_key = os.getenv("PHRASE_SEED")
    # model = "gpt-4",
    # model = 'gpt-4-32k-0314',
    # model = "gpt-3.5-turbo",
    # model = 'gpt-3.5-turbo-16k'
    answer = openai.ChatCompletion.create(
        model = model,
        messages=prompt
    )
    return answer


@app.route("/start", methods=["POST"])
def call_start():
    r = request.get_json()
    logger.info("call_start")
    result = "Welcome to the chatbot service. Please type your question."
    return jsonify({"result": result})


def save_message(user_id, user_name, chat_id, chat_type, message):
    date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    if chat_type == 'group' or chat_type == 'supergroup':
        logger.info("group chat")
        # Create group id folder in the data path if not exist
        group_path = f"data/groups/{chat_id}"
        if not os.path.exists(group_path):
            os.makedirs(group_path)
        # Each message saved as a new file with date and user name in a filename
        file_name = f"{group_path}/{date_time}_{user_name}.txt"
        with open(file_name, "w") as f:
            f.write(message)
    else:
        logger.info("private chat")
        # Create user id folder in the data path if not exist
        user_path = f"data/users/{user_id}"
        if not os.path.exists(user_path):
            os.makedirs(user_path)
        # Each message saved as a new file with date and user name in a filename
        file_name = f"{user_path}/{date_time}_{user_name}.txt"


@app.route("/message", methods=["POST"])
def call_message():
    logger.info("message")
    r = request.get_json()
    # Assuming r is a JSON-formatted string
    r_dict = json.loads(r)
    user_id = r_dict["user_id"]
    user_name = r_dict["user_name"]
    chat_id = r_dict["chat_id"]
    chat_type = r_dict["chat_type"]
    message = r_dict["message"]
    # Save the message
    save_message(user_id, user_name, chat_id, chat_type, message)
    # Define the default answer
    result = ""

    return jsonify({"result": result})


@app.route("/inline", methods=["POST"])
def call_inline_rev0():
    r = request.get_json()
    logger.info("request data: {}".format(r))    
    # Assuming r is a JSON-formatted string
    r_dict = json.loads(r)
    user_id = r_dict["user_id"]
    logger.info("user_id: {}".format(user_id))

    # request_str = json.loads(str(await request.text()))
    # data = json.loads(request_str)
    # user_id = str(data['user_id'])
    # logging.info(str(dt.now())+' '+'User: '+str(user_id)+' call_inline')
    # read user config
    # config = read_config(user_id)
    # content = config['chat_gpt_prompt'][-1]['content']
    # logging.info(str(dt.now())+' '+'User: '+str(user_id)+' call_inline.response '+content)
    # return web.Response(text=content, content_type="text/html")



    
    # Read userlist from data/users.txt
    """with open("data/access.txt", "r") as f:
        userlist = f.read().splitlines()
    # replace new line
    userlist = [int(x) for x in userlist]

    if user_id not in userlist:
        logger.info("User not allowed: {}".format(user_id))
        return jsonify({"result": "You are not allowed to access this service"})
    
    # Check if the user is within the request frequency limit
    user_file = f"data/calls/{user_id}.txt"
    if os.path.exists(user_file):
        with open(user_file, "r") as f:
            last_request_time = datetime.datetime.strptime(f.read(), "%Y-%m-%d %H:%M:%S.%f")
        if (datetime.datetime.now() - last_request_time).seconds < 20:
            elapsed_time = (datetime.datetime.now() - last_request_time).seconds
            return jsonify({"result": f"You must wait {20 - elapsed_time} seconds before the next request"})

    # if user_id in userlist:
    logger.info("inline query: {}".format(r_dict["query"]))
    query = r_dict["query"]
    openai.api_key = os.getenv("PHRASE_SEED")
    answer = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    # model='gpt-3.5-turbo-16k',
    max_tokens=500,
    messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": str(query)}
    ]    
    )
    logger.info("answer: {}".format(answer))
    result = answer['choices'][0]['message']['content']"""

    """else:
        logger.info("User not allowed: {}".format(user_id))
        result = "You are not allowed to access this service"
    """
    # Save the current time as the last request time
    """with open(user_file, "w") as f:
        f.write(str(datetime.datetime.now()))"""
    result = 'inline'
    return jsonify({"result": result})


if __name__ == "__main__":
    app.run(
        host='0.0.0.0',
        debug=False,
        port=int(os.environ.get("PORT", 10000))
        )