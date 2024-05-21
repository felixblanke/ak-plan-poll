import json
from pathlib import Path

from flask import Flask, render_template, url_for, request
from werkzeug.security import safe_join
from markupsafe import escape
import uuid

app = Flask(__name__)
app.config["DATA_DIR"] = "data"
app.config["EXPORT_DIR"] = "export"
app.config.from_file("config.json", load=json.load, silent=True)


def read_ak_data(poll_name: str) -> dict | None:
    path = Path(safe_join(app.config["DATA_DIR"], f"{poll_name}.json"))
    try:
        with path.open("r") as ff:
            return json.load(ff)
    except:
        return None


def read_ak_list(data: dict, default: list[str] | None = None) -> list[str] | None:
    try:
        return [ak["info"] for ak in data["aks"]]
    except KeyError:
        return default


def read_block_list(data: dict, default: list[str] | None = None) -> list[str] | None:
    try:
        return data["timeslots"]["info"]["blocknames"]
    except:
        return default


def read_info(data: dict, key: str, default: str | None = None) -> str | None:
    try:
        return data["info"][key]
    except:
        return default


@app.route("/<poll_name>", methods=["POST"])
def post_result(poll_name: str):
    participant = {
        "preferences": [],
        "required_time_constraints": [f"notblock{i}" for i in range(7)],
    }
    # TODO: replace hardcoded num blocks by reasonable code

    participant["info"] = {
        "name": request.form["name"],
        "uni": request.form["uni"],
        "remarks": request.form["remarks"],
    }

    for key, val in request.form.items():
        if key.startswith("ak"):
            preference_score = int(val)
            participant["preferences"].append(
                {
                    "ak_id": key,
                    "required": preference_score == -1,
                    "preference_score": preference_score,
                }
            )
        elif key.startswith("block"):
            # here we only get the checked boxes, so we remove those from the set of all boxes set above
            participant["required_time_constraints"].remove("not" + key)

    export_dir = Path(app.config["EXPORT_DIR"]) / poll_name
    export_dir.mkdir(exist_ok=True, parents=True)

    ak_uuid = uuid.uuid1()
    with (export_dir / f"{ak_uuid}.json").open("w") as ff:
        json.dump(participant, ff, indent=4, ensure_ascii=False)

    return render_template(
        "success.html",
        participant=json.dumps(participant, indent=4, ensure_ascii=False),
    )


@app.route("/", methods=["GET"])
def landing_page():
    return render_template("unknown.html")


@app.route("/<poll_name>", methods=["GET"])
def get_form(poll_name: str):
    if (data := read_ak_data(poll_name)) is not None:
        ak_list = read_ak_list(data, default=[])
        block_list = read_block_list(data, default=[])
        title = read_info(data, key="title", default=poll_name)
        block_info_html = read_info(data, key="block_info_html")
        ak_info_html = read_info(data, key="ak_info_html")

        return render_template(
            "poll.html",
            poll_name=escape(poll_name),
            ak_list=ak_list,
            block_list=block_list,
            title=escape(title),
            block_info_html=block_info_html, # Do not escape!
            ak_info_html=ak_info_html, # Do not escape!
        )
    else:
        return render_template("unknown.html")
