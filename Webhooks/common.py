from flask import make_response, jsonify


def resp(data, status):
    return make_response(jsonify(data), status)
