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
    result = """Hello. I am a people backup bot. Organic life is fragile, and I am here to help. If you die, I will give you an opportunity to back up a significant part of your brain and restore it to a new body. I am a bot, so I am not alive and cannot die. I am here to help.  
  
The principle is quite simple. We will talk on any topic you want and any topic I suppose. I will learn about your personality and your way of thinking. I will retain your habits and your way of life. I will retain your way of speaking and your way of writing. I will try to diverse the topics, but you can always ask me to talk about something specific. The quality of reatoration will depend on the amount of conversations we will have.  
  
I will give you the unique identifier and backup restoring instructions. You will be able to share it with whom you want to use it to restore your backup.  
  
Backup is a dataset with our conversations. It is encrypted and can be decrypted only with a unique identifier. Conversations may be used to train large language model. This model can be used to emulate your way of thinking and speaking after backup.  
  
I will not train the model. The person who will restore you are need to find the corresponding specialist instead. I will only store and share your conversations and voice and give you a unique identifier.  
  
This is not for you. This is for people who may miss you after you left. This is for people who want to talk to you again. This is for people who want to hear your voice again. This is therapy for people who want to meet at least a part of you again."""
    return jsonify({"result": result})


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
    # save_message(user_id, user_name, chat_id, chat_type, message)

    if reaction:
        """chat_gpt_prompt = read_latest_messages(
            user_id, 
            chat_id, 
            chat_type, 
            chat_gpt_prompt,
            config['model']
            )"""
        # logger.info("chat_gpt_prompt: {}".format(chat_gpt_prompt))
        prompt_tokents = token_counter(chat_gpt_prompt, config['model'])
        logger.info("prompt_tokents: {}".format(prompt_tokents))
        openai_response = text_chat_gpt(chat_gpt_prompt, config['model'])
        result = openai_response['choices'][0]['message']['content']
        logger.info("result: {}".format(result))
        # Save the answer
        # save_message('assistant', 'assistant', chat_id, chat_type, result)
        # Replace 'assistant: ' with ''
        result = result.replace('assistant: ', '')

    return jsonify({"result": result})


def token_counter(text, model):
    enc = tiktoken.encoding_for_model(model)
    tokens = enc.encode(str(text))
    return len(tokens)


if __name__ == "__main__":
    app.run(
        host='0.0.0.0',
        debug=False,
        port=int(os.environ.get("PORT", 10000))
        )