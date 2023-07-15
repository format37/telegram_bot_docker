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
import pandas as pd


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


@app.route("/start", methods=["POST"])
def call_start():
    r = request.get_json()
    logger.info("call_start_test")
    result = """Hello,  
I am a people backup bot, designed to safeguard the memories and personalities of individuals due to the fragile nature of organic life and memory. As a bot, I do not possess life, nor can I die. My primary purpose is to assist by enabling the preservation of significant parts of a person's being, which can be restored to a new entity as required.  
  
The principle is quite simple. We will talk on any topic you want and any topic that I will propose. I will learn about your personality and your way of thinking. I will retain your habits and your way of life. I will retain your way of speaking and your way of writing. I will try to diversify the topics, but you can always ask me to talk about something specific. The quality of restoration will depend on the number of conversations we will have.  
The advantage of this approach in comparison with using randomized chat dumps, and written books is in our goal of the conversation. The goal is to restore as full and as precise as possible. The topics and questions will be selected to achieve this goal.  
Be yourself and imagine that you're speaking with someone who has revived you. This will better meet their expectations. And I will try to anticipate the questions and topics that will be asked of you, subtly weaving them into our conversation.  
  
I will give you the unique identifier and backup restoring instructions. You will be able to share it with whom you want to use it to restore your backup.  
  
Backup is a dataset with our conversations. It is encrypted and can be decrypted only with a unique identifier. Conversations may be used to train large language models. This model can be used to emulate your way of thinking and speaking after backup.  
  
I will not train the model. The person who will restore you are need to find the corresponding specialist instead. I will only store and share your dataset: conversations, voice, and access key.  
  
This will not be made for you. This is needed for people who may miss you after you left. This is for people who want to talk to you again. This is for people who want to hear your voice again. This is therapy for people who want to meet at least a part of you again."""
    logger.info("result: {}".format(result))
    return jsonify({"result": result})


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


def save_message(speaker, conversation_id, message, user_id):
    # Set the filename as the user_id
    filename = f'user_conf/{user_id}/conversations.csv'
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Get the current date and time
    now = datetime.datetime.now()
    date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
    
    # Get the number of messages already in the conversation
    if os.path.exists(filename):
        df = pd.read_csv(filename)
        message_id = len(df)
    else:
        df = pd.DataFrame(columns=['conversation_id', 'message_id', 'date_time', 'speaker', 'message'])
        message_id = 0

    # Append the new message to the conversation
    df = df.append({
        'conversation_id': conversation_id, 
        'message_id': message_id, 
        'date_time': date_time, 
        'speaker': speaker, 
        'message': message
        }, ignore_index=True)
    df.to_csv(filename, index=False)


def read_latest_messages(user_id, chat_gpt_prompt):
    # Set the filename as the user_id
    filename = f'user_conf/{user_id}/conversations.csv'
    
    # Check if the file exists
    if os.path.exists(filename):
        # Load the conversations
        df = pd.read_csv(filename)
        
        # Get the latest conversation_id
        latest_conversation_id = df['conversation_id'].max()

        # Get the messages from the latest conversation
        latest_messages_df = df[df['conversation_id'] == latest_conversation_id]

        # Convert the messages to the required format
        for i, row in latest_messages_df.iterrows():
            if row['speaker'] == user_id:
                role = 'user'
            else:
                role = 'assistant'

            message = {"role": role, "content": row['message']}
            chat_gpt_prompt.append(message)

    return chat_gpt_prompt


@app.route("/message", methods=["POST"])
def call_message():
    logger.info("message")
    r = request.get_json()
    # Assuming r is a JSON-formatted string
    r_dict = json.loads(r)
    user_id = r_dict["user_id"]
    user_name = r_dict["user_name"]
    message = r_dict["text"]
    
    # Define the default answer
    result = ""
    config = read_config(user_id)
            
    # Define the prompt
    # chat_gpt_prompt =  [{"role": "system", "content": "I am a Digital Continuity Assistant."}],
    chat_gpt_prompt = config['chat_gpt_prompt']    
    # Save the original message
    save_message(user_name, config['conversation_id'], message, user_id)
    # chat_gpt_prompt =  [{"role": "system", "content": "I am a Digital Continuity Assistant."}, {"role": "user", "content": message}]
    chat_gpt_prompt = read_latest_messages(
        user_id, 
        chat_gpt_prompt
        )
    # logger.info("chat_gpt_prompt: {}".format(chat_gpt_prompt))
    prompt_tokents = token_counter(chat_gpt_prompt, config['model'])
    logger.info("prompt_tokents: {}".format(prompt_tokents))
    openai_response = text_chat_gpt(chat_gpt_prompt, config['model'])
    result = openai_response['choices'][0]['message']['content']
    logger.info("result: {}".format(result))
    # Save the answer
    # save_message('assistant', 'assistant', chat_id, chat_type, result)
    save_message('assistant', config['conversation_id'], result, user_id)
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