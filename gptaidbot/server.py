import os
import time
from flask import Flask, request, jsonify, Response
import logging
import json
import openai
import datetime
import json
import glob
import tiktoken


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
        logger.info("group chat: "+str(chat_id))
        # Create group id folder in the data path if not exist
        group_path = os.path.join("data", "groups", str(chat_id))
        os.makedirs(group_path, exist_ok=True)
        # Each message saved as a new file with date in a filename
        file_name = f"{date_time}.json"
        with open(os.path.join(group_path, file_name), "w") as f:
            json.dump(data, f)
    else:
        logger.info("private chat: "+str(user_id))
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
    

def read_latest_messages(user_id, chat_id, chat_type, chat_gpt_prompt_original, model):
    
    if chat_type == 'group' or chat_type == 'supergroup':
        logger.info("read group chat")
        path = os.path.join("data", "groups", str(chat_id))
    else:
        logger.info("read private chat")
        path = os.path.join("data", "users", str(user_id))

    chat_gpt_prompt = []
    token_limit = 2000

    list_of_files = glob.glob(path + "/*.json")
    list_of_files.sort(key=os.path.getctime, reverse=True)

    limit_reached = False
    for file_name in list_of_files:
        logger.info("reading file: "+file_name)
        if limit_reached == False and token_counter(chat_gpt_prompt, model)<token_limit:            
            with open(file_name, "r") as f:
                data = json.load(f)
                if data["user_name"] == "assistant":
                    role = "assistant"
                    chat_gpt_prompt.append({"role": role, "content": data["message"]})
                else:
                    role = "user"
                    user_name = data["user_name"]
                    user_name = user_name if user_name else "Unknown"
                    chat_gpt_prompt.append({"role": role, "content": user_name +': '+ data["message"]})
        else:
            limit_reached = True
            logger.info("token limit reached. removing file: "+file_name)
            os.remove(file_name) 

    chat_gpt_prompt.reverse()
    for item in chat_gpt_prompt:
        chat_gpt_prompt_original.append(item)

    logger.info("chat_gpt_prompt_original: "+str(chat_gpt_prompt_original))

    return chat_gpt_prompt_original


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
        if message.startswith("/*") and len(message.strip()) > 2:
            reaction = True
            message = message[2:].strip()
    else:
        # reaction = True
        reaction = False # TODO: remove this line
        config = read_config(user_id)
            
    # Define the prompt
    chat_gpt_prompt = config['chat_gpt_prompt']
    # Save the original message
    save_message(user_id, user_name, chat_id, chat_type, message)

    if reaction:
        chat_gpt_prompt = read_latest_messages(
            user_id, 
            chat_id, 
            chat_type, 
            chat_gpt_prompt,
            config['model']
            )
        # logger.info("chat_gpt_prompt: {}".format(chat_gpt_prompt))
        prompt_tokents = token_counter(chat_gpt_prompt, config['model'])
        logger.info("prompt_tokents: {}".format(prompt_tokents))
        openai_response = text_chat_gpt(chat_gpt_prompt, config['model'])
        result = openai_response['choices'][0]['message']['content']
        logger.info("result: {}".format(result))
        # Save the answer
        save_message('bot', 'bot', chat_id, chat_type, result)
        # Replace 'bot: ' with ''
        result = result.replace('bot: ', '')

    return jsonify({"result": result})


def token_counter(text, model):
    enc = tiktoken.encoding_for_model(model)
    tokens = enc.encode(str(text))
    return len(tokens)


@app.route("/inline", methods=["POST"])
def call_inline():
    r = request.get_json()
    logger.info("request data: {}".format(r))
    # Assuming r is a JSON-formatted string
    r_dict = json.loads(r)
    user_id = r_dict["user_id"]
    logger.info("user_id: {}".format(user_id))
    result = 'inline'
    return jsonify({"result": result})


if __name__ == "__main__":
    app.run(
        host='0.0.0.0',
        debug=False,
        port=int(os.environ.get("PORT", 10000))
        )