import json
from pathlib import Path

from flask import Flask, render_template, url_for, request
from werkzeug.security import safe_join
from markupsafe import escape
import uuid

app = Flask(__name__)
# app.config.from_file("config.json", load=json.load)


def read_ak_list(poll_name: str) -> list[str] | None:
    path = Path(safe_join("data", f"{poll_name}.json"))
    if path.exists():
        with path.open("r") as ff:
            ak_data = json.load(ff)
        return [ak["info"] for ak in ak_data["aks"]]
    else:
        return None


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

    export_dir = Path("export")
    export_dir.mkdir(exist_ok=True)

    ak_uuid = uuid.uuid4()
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
    if (ak_list := read_ak_list(poll_name)) is not None:
        return render_template(
            "poll.html", poll_name=escape(poll_name), ak_list=ak_list
        )
    else:
        return render_template("unknown.html")
