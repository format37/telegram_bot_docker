import os
import time
from flask import Flask, request, jsonify, Response
import logging
import json
import openai
import datetime
import json
import glob


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


def load_default_config(user_id):
    conf_path = 'user_conf/'
    with open(conf_path+'config.json', 'r') as f:
        config = json.load(f)
    
    return config


def read_config(user_id):
    conf_path = 'user_conf/'
    user_id = str(user_id)
    # if user.json conf not in user_conf folder, create it
    # default config file: config.json
    if not os.path.exists(conf_path+user_id+'.json'):
        config = load_default_config(user_id)
    else:
        with open(conf_path+user_id+'.json', 'r') as f:
            config = json.load(f)
    return config


@app.route("/start", methods=["POST"])
def call_start():
    r = request.get_json()
    logger.info("call_start")
    result = "Welcome to the chatbot service. Please type your question."
    return jsonify({"result": result})


def save_message(user_id, user_name, chat_id, chat_type, message):
    date_time = datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S_%f")
    data = {
        "user_id": user_id,
        "user_name": user_name,
        "message": message,
    }
    if chat_type == 'group' or chat_type == 'supergroup':
        logger.info("group chat")
        # Create group id folder in the data path if not exist
        group_path = os.path.join("data", "groups", str(chat_id))
        os.makedirs(group_path, exist_ok=True)
        # Each message saved as a new file with date in a filename
        file_name = f"{date_time}.json"
        with open(os.path.join(group_path, file_name), "w") as f:
            json.dump(data, f)
    else:
        logger.info("private chat")
        # Create user id folder in the data path if not exist
        user_path = os.path.join("data", "users", str(user_id))
        os.makedirs(user_path, exist_ok=True)
        # Each message saved as a new file with date in a filename
        file_name = f"{date_time}.json"
        with open(os.path.join(user_path, file_name), "w") as f:
            json.dump(data, f)

def read_latest_message(user_id, chat_id, chat_type):
    if chat_type == 'group' or chat_type == 'supergroup':
        logger.info("read group chat")
        # Create group id folder in the data path if not exist
        group_path = os.path.join("data", "groups", str(chat_id))
        # Get the latest file in folder
        list_of_files = glob.glob(group_path + "/*.json")
        latest_file = max(list_of_files, key=os.path.getctime)
        with open(latest_file, "r") as f:
            data = json.load(f)
        return data["message"]
    else:
        logger.info("read private chat")
        # Create user id folder in the data path if not exist
        user_path = os.path.join("data", "users", str(user_id))
        # Get the latest file in folder
        list_of_files = glob.glob(user_path + "/*.json")
        latest_file = max(list_of_files, key=os.path.getctime)
        with open(latest_file, "r") as f:
            data = json.load(f)
        return data["message"]
    

def read_latest_messages(user_id, chat_id, chat_type, chat_gpt_prompt):
    # messages = []
    if chat_type == 'group' or chat_type == 'supergroup':
        logger.info("read group chat")
        # Create group id folder in the data path if not exist
        group_path = os.path.join("data", "groups", str(chat_id))
        # Get all files in folder
        list_of_files = glob.glob(group_path + "/*.json")
    else:
        logger.info("read private chat")
        # Create user id folder in the data path if not exist
        user_path = os.path.join("data", "users", str(user_id))
        # Get all files in folder
        list_of_files = glob.glob(user_path + "/*.json")

    # Sort files by creation time
    list_of_files.sort(key=os.path.getctime)

    # Iterate over sorted files and append message to messages list
    for file_name in list_of_files:
        with open(file_name, "r") as f:
            data = json.load(f)
            # messages.append(data["user_name"]+': '+data["message"])
            # chat_gpt_prompt.append({"role": "user", "content": str(message)})
            chat_gpt_prompt.append({"role": data["user_name"], "content": data["message"]})
            
    return chat_gpt_prompt


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
    message = r_dict["text"]
    
    # Define the default answer
    result = ""
    reaction = False
    if chat_type == 'group' or chat_type == 'supergroup':
        # Read config
        config = read_config(chat_id)
        
        if message.startswith("/?") and len(message.strip()) > 2:
            # logger.info("group chat")
            reaction = True
            message = message[2:].strip()
            # chat_gpt_prompt.append({"role": "user", "content": str(message)})            
            # result = read_latest_messages(user_id, chat_id, chat_type)
            # Call GPT
            """answer = text_chat_gpt(chat_gpt_prompt, config['model'])
            # Get the answer
            result = answer["choices"][0]["text"]
            # Save the message
            save_message('system', 'system', chat_id, chat_type, result)"""            
    else:
        config = read_config(user_id)
        reaction = True
    
    # Define the prompt
    chat_gpt_prompt = config['chat_gpt_prompt']
    # Save the original message
    save_message(user_id, user_name, chat_id, chat_type, message)

    chat_gpt_prompt = read_latest_messages(
        user_id, 
        chat_id, 
        chat_type, 
        chat_gpt_prompt
        )
    
    result = str(chat_gpt_prompt)
    # chat_gpt_prompt.append({"role": "user", "content": str(message)})
    # try:
    # openai_response = text_chat_gpt(chat_gpt_prompt, config['model'])
    # result = openai_response['choices'][0]['message']['content']
    
    """except Exception as e:
        err = "Error: {}".format(e)
        logger.info(err)
        openai_response = err"""
    
    # Save the answer
    save_message('system', 'system', chat_id, chat_type, result)

    return jsonify({"result": result})


@app.route("/inline", methods=["POST"])
def call_inline():
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