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


def read_ak_list(poll_name: str) -> list[str] | None:
    path = Path(safe_join(app.config["DATA_DIR"], f"{poll_name}.json"))
    if path.exists():
        with path.open("r") as ff:
            ak_data = json.load(ff)
        return [ak["info"] for ak in ak_data["aks"]]
    else:
        return None


def read_block_list(poll_name: str) -> list[str] | None:
    path = Path(safe_join("data", f"{poll_name}.json"))
    if path.exists():
        with path.open("r") as ff:
            data = json.load(ff)
        return data["timeslots"]["info"]["blocknames"]
    else:
        return None


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
    if (ak_list := read_ak_list(poll_name)) is not None and (
        block_list := read_block_list(poll_name)
    ) is not None:
        return render_template(
            "poll.html",
            poll_name=escape(poll_name),
            ak_list=ak_list,
            block_list=block_list,
            title=escape(poll_name),
        )
    else:
        return render_template("unknown.html")
