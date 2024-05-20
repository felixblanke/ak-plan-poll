import json

from flask import Flask, render_template, url_for, request

app = Flask(__name__)
# app.config.from_file("config.json", load=json.load)

with open("aks.json", "r") as ff:
    ak_dict = json.load(ff)

@app.route("/<poll_name>", methods=["POST"])
def post_result(poll_name: str):
    participant = {"preferences": []}

    participant["info"] = {
        "name": request.form["name"],
        "uni": request.form["uni"],
        "remarks": request.form["remarks"],
    }

    for key, val in request.form.items():
        if not key.startswith("ak"):
            continue

        preference_score = int(val)

        participant["preferences"].append(
            {
                "ak_id": key,
                "required": preference_score == -1,
                "preference_score": preference_score,
            }
        )
    return render_template(
        "success.html",
        participant=json.dumps(participant, indent=4, ensure_ascii=False),
    )


@app.route("/", methods=["GET"])
def landing_page():
    return render_template("unknown.html")


@app.route("/<poll_name>", methods=["GET"])
def get_form(poll_name: str):
    if (ak_list := ak_dict.get(poll_name, None)) is not None:
        return render_template("poll.html", poll_name=poll_name, ak_list=ak_list)
    else:
        return render_template("unknown.html")
