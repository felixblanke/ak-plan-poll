import json

from flask import Flask, render_template, url_for, request

app = Flask(__name__)
app.config.from_file("config.json", load=json.load)

def dumm_get_aks(poll_name: str) -> list[str]:
    ak_dict = {
        "koma90-test": ["AK Berufungshandbuch", "AK Testwurst"]
    }
    return ak_dict.get(poll_name, None)


@app.route("/<poll_name>", methods=["POST"])
def post_result(poll_name: str):
    # TODO: Process request
    print(request.form)
    return render_template("success.html")

@app.route("/", methods=["GET"])
def landing_page():
    return render_template("unknown.html")

@app.route("/<poll_name>", methods=["GET"])
def get_form(poll_name: str):
    ak_list = dumm_get_aks(poll_name=poll_name)
    if ak_list is None:
        return render_template("unknown.html")
    else:
        return render_template("poll.html", poll_name=poll_name, ak_list=ak_list)
