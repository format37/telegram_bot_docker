import os
from flask import Flask, request, jsonify, Response
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = Flask(__name__)

@app.route("/test")
def call_test():
    return "get ok"

@app.route("/request", methods=["POST"])
def call_request():
    r = request.get_json()
    logger.info("request data: {}".format(r))
    # INFO:__main__:request data: {"user_id": 106129214}
    # Assuming r is a JSON-formatted string
    r_dict = json.loads(r)
    user_id = r_dict["user_id"]
    logger.info("user_id: {}".format(user_id))
    # INFO:__main__:user_id: 106129214
    return jsonify({"user_id": user_id})


if __name__ == "__main__":
    app.run(
        host='0.0.0.0',
        debug=False,
        port=int(os.environ.get("PORT", 10000))
        )