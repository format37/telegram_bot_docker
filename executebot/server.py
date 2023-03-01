import os
from flask import Flask, request, jsonify, Response
import logging

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
	user_id = r["user_id"]
	return jsonify({"text": user_id})


if __name__ == "__main__":
    app.run(
		host='0.0.0.0',
		debug=False,
		port=int(os.environ.get("PORT", 10000))
		)