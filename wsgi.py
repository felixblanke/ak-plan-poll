import json
import uuid
from collections import defaultdict
from pathlib import Path

from flask import Flask, redirect, render_template, request, url_for
from markupsafe import escape
from werkzeug.security import safe_join

app = Flask(__name__)
app.config["DATA_DIR"] = "data"
app.config["EXPORT_DIR"] = "export"
app.config["DEFAULT_DURATION"] = 2
app.config.from_file("config.json", load=json.load, silent=True)


def get_data_file(poll_name: str) -> Path:
    return Path(safe_join(app.config["DATA_DIR"], f"{poll_name}.json"))


def get_export_dir(poll_name: str) -> Path:
    return Path(safe_join(app.config["EXPORT_DIR"], poll_name))


def read_ak_data(poll_name: str) -> dict | None:
    try:
        with get_data_file(poll_name).open("r") as ff:
            return json.load(ff)
    except (OSError, json.decoder.JSONDecodeError):
        return None


def write_ak_data(poll_name: str, data: dict) -> dict | None:
    with get_data_file(poll_name).open("w") as ff:
        return json.dump(data, ff, indent=2, ensure_ascii=False)


def read_ak_list(data: dict, default: list[str] | None = None) -> list[str] | None:
    try:
        return data["aks"]
    except KeyError:
        return default


def read_blocks(
    data: dict, default: dict | None = None
) -> dict[str, list[tuple[int, str]]] | None:
    try:
        blocknames = data["timeslots"]["info"]["blocknames"]
        block_dir = defaultdict(list)
        for slot_idx, (day, block_name) in enumerate(blocknames):
            block_dir[day].append((slot_idx, block_name))
        return block_dir
    except KeyError:
        return default


def read_info(data: dict, key: str, default: str | None = None) -> str | None:
    try:
        return data["info"][key]
    except KeyError:
        return default


@app.route("/<poll_name>", methods=["POST"])
def post_result(poll_name: str):
    num_blocks = len(read_blocks(read_ak_data(poll_name), default={}))

    participant = {
        "preferences": [],
        "time_constraints": [f"notblock{i}" for i in range(num_blocks)],
    }

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
            # here we only get the checked boxes
            # so we remove those from the set of all boxes set above
            participant["time_constraints"].remove("not" + key)

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
        place = read_info(data, key="place")

        if place:
            title += f" in {place}"

        return render_template(
            "poll.html",
            poll_name=escape(poll_name),
            aks=ak_list,
            blocks=block_dict.items(),
            title=escape(title),
            block_info_html=block_info_html,  # Do not escape!
            ak_info_html=ak_info_html,  # Do not escape!
        )
    else:
        return render_template("unknown.html")


@app.route("/create/<poll_name>", methods=["GET", "POST"])
def create_poll(poll_name: str):
    data = read_ak_data(poll_name)
    if data is None:
        data = {"aks": []}

    if request.method == "POST":
        form_data = dict(request.form)

        ak_dict = defaultdict(lambda: defaultdict(dict))

        for key, val in form_data.items():
            if key.split("_")[0] == "akneu":
                continue
            ak_id = int(key.split("_")[0][2:])
            field = key.split("_")[1]
            if field in ["duration"]:
                # keys not in info:
                ak_dict[ak_id][field] = int(val)
            else:
                ak_dict[ak_id]["info"][field] = val

        data["aks"] = list(
            map(lambda x: x[1], sorted(ak_dict.items(), key=lambda x: x[0]))
        )

        new_ak_dict = {}
        if form_data["akneu_name"]:
            new_ak_dict["name"] = form_data["akneu_name"]
            new_ak_dict["description"] = form_data["akneu_description"]
            new_ak_dict["head"] = form_data["akneu_head"]
            if "akneu_reso" in form_data.keys():
                new_ak_dict["reso"] = True

            new_ak_dict = {
                "info": new_ak_dict,
                "duration": int(form_data["akneu_duration"]),
            }

        for v in ak_dict.values():
            if "reso" not in v["info"]:
                v["info"]["reso"] = False

        if new_ak_dict:
            data["aks"].append(new_ak_dict)

        write_ak_data(poll_name, data)

        return redirect(url_for("create_poll", poll_name=poll_name))

    title = read_info(data, key="title", default=poll_name)
    ak_list = read_ak_list(data, default=[])

    return render_template(
        "create.html",
        title=title,
        aks=ak_list,
        poll_name=poll_name,
        default_duration=app.config["DEFAULT_DURATION"],
    )


@app.route("/result/<poll_name>", methods=["GET"])
def show_results(poll_name: str):
    export_dir = Path(app.config["EXPORT_DIR"]) / poll_name

    if (data := read_ak_data(poll_name)) is not None:
        title = read_info(data, key="title", default=poll_name)
        ak_list = read_ak_list(data, default=[])
        block_dict = read_blocks(data, default={})
        ak_pref_dict = defaultdict(lambda: defaultdict(int))
        time_constraint_dict = defaultdict(lambda: defaultdict(int))
        block_lst = []
        for day, day_entries in block_dict.items():
            block_lst.extend(
                [f"{day[:2]} {slot_name}" for block_idx, slot_name in day_entries]
            )
        for result_json in export_dir.glob("*.json"):
            with result_json.open("r") as ff:
                result_dict = json.load(ff)
            for pref in result_dict["preferences"]:
                ak_id = int(pref["ak_id"][2:])
                ak_name = ak_list[ak_id]["name"]
                ak_pref_dict[ak_name][pref["preference_score"]] += 1
                if pref["preference_score"] == 0:
                    continue
                for time_constr in result_dict["time_constraints"]:
                    time_contr_idx = int(time_constr[len("notblock") :])
                    time_constraint_dict[ak_name][block_lst[time_contr_idx]] += 1

        ak_pref_dict = {k: dict(v) for k, v in ak_pref_dict.items()}
        for k in ak_pref_dict:
            ak_pref_dict[k]["time_constraints"] = dict(time_constraint_dict[k])
        return render_template(
            "result.html",
            title=escape(title),
            aks=ak_pref_dict.items(),
            num_participants=len(list(export_dir.glob("*.json"))),
        )
    else:
        return render_template("unknown.html")
