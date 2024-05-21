from collections import defaultdict
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


def read_blocks(data: dict, default: dict | None = None) -> dict[str, list[tuple[int, str]]] | None:
    try:
        blocknames = data["timeslots"]["info"]["blocknames"]
        block_dir = defaultdict(list)
        for slot_idx, (day, block_name) in enumerate(blocknames):
            block_dir[day].append((slot_idx, block_name))
        return block_dir
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
        block_dict = read_blocks(data, default={})
        title = read_info(data, key="title", default=poll_name)
        block_info_html = read_info(data, key="block_info_html")
        ak_info_html = read_info(data, key="ak_info_html")

        return render_template(
            "poll.html",
            poll_name=escape(poll_name),
            aks=ak_list,
            blocks=block_dict.items(),
            title=escape(title),
            block_info_html=block_info_html, # Do not escape!
            ak_info_html=ak_info_html, # Do not escape!
        )
    else:
        return render_template("unknown.html")


@app.route("/result/<poll_name>", methods=["GET"])
def show_results(poll_name: str):
    export_dir = Path(app.config["EXPORT_DIR"]) / poll_name

    if (data := read_ak_data(poll_name)) is not None:
        title = read_info(data, key="title", default=poll_name)
        ak_list = read_ak_list(data, default=[])
        # print(ak_list)
        ak_pref_dict = defaultdict(lambda: defaultdict(int))
        time_constraint_dict = defaultdict(lambda: defaultdict(int))
        for result_json in export_dir.glob("*.json"):
            with result_json.open("r") as ff:
                result_dict = json.load(ff)
            for pref in result_dict["preferences"]:
                ak_id = int(pref["ak_id"][2:])
                ak_name = ak_list[ak_id]["name"]
                ak_pref_dict[ak_name][pref["preference_score"]] += 1
                if pref["preference_score"] == 0:
                    continue
                for time_constr in result_dict["required_time_constraints"]:
                    time_constraint_dict[ak_name][time_constr] += 1

        ak_pref_dict = {k: dict(v) for k, v in ak_pref_dict.items()}
        for k in ak_pref_dict:
            ak_pref_dict[k]["time_constraints"] = dict(time_constraint_dict[k])
        return render_template("result.html", title=escape(title), aks=ak_pref_dict.items(), num_participants=len(list(export_dir.glob("*.json"))))
    else:
        return render_template("unknown.html")
