import os
from flask import Flask, request, jsonify, Response
import logging
import json
import openai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = Flask(__name__)

@app.route("/test")
def call_test():
    return "get ok"


@app.route("/start", methods=["POST"])
def call_start():
    r = request.get_json()
    logger.info("request data: {}".format(r))
    # Assuming r is a JSON-formatted string
    r_dict = json.loads(r)
    user_id = r_dict["user_id"]
    logger.info("user_id: {}".format(user_id))
    # Read userlist from data/users.txt
    with open("data/access.txt", "r") as f:
        userlist = f.read().splitlines()
    # replace new line
    userlist = [int(x) for x in userlist]
    logger.info("userlist: {}".format(userlist))
    if user_id in userlist:
        result = "ok"
    else:
        result = "You are not allowed to access this service"

    return jsonify({"result": result})


@app.route("/inline", methods=["POST"])
def call_inline():
    r = request.get_json()
    logger.info("request data: {}".format(r))
    # Assuming r is a JSON-formatted string
    r_dict = json.loads(r)
    user_id = r_dict["user_id"]
    logger.info("user_id: {}".format(user_id))
    # Read userlist from data/users.txt
    with open("data/access.txt", "r") as f:
        userlist = f.read().splitlines()
    # replace new line
    userlist = [int(x) for x in userlist]
    logger.info("userlist: {}".format(userlist))
    if user_id in userlist:
        
        query = r_dict["query"]
        openai.api_key = os.getenv("PHRASE_SEED")
        answer = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": str(query)}
            ]
        )
        logger.info("answer: {}".format(answer))
        result = answer['choices'][0]['message']['content']

    else:
        result = "You are not allowed to access this service"
    return jsonify({"result": result})


if __name__ == "__main__":
    app.run(
        host='0.0.0.0',
        debug=False,
        port=int(os.environ.get("PORT", 10000))
        )