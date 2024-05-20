import json

from flask import Flask, render_template, url_for, request

app = Flask(__name__)
app.config.from_file("config.json", load=json.load)

@app.route("/<poll_name>", methods=["POST"])
def post_result(poll_name: str):
    # TODO: Process request
    print(request.form)
    return render_template("success.html")


@app.route("/<poll_name>", methods=["GET"])
def get_form(poll_name: str):
    return render_template("poll.html", poll_name=poll_name)
