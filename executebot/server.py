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
	var_a = int(r["var_a"])
	var_b = int(r["var_b"])
	var_c = var_a + var_b
	return jsonify({"var_c": var_c})


if __name__ == "__main__":
    app.run(
		host='0.0.0.0',
		debug=False,
		port=int(os.environ.get("PORT", 10000))
		)