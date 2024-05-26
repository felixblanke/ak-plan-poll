import json
from pathlib import Path
from typing import Iterable

import fire

from wsgi import get_export_dir, read_ak_data, write_ak_data


def clean_data(poll_name: str, default_duration: int = 2) -> None:
    data = read_ak_data(poll_name)
    for idx, ak in enumerate(data["aks"]):
        if "required_time_constraints" in ak:
            ak["time_constraints"] = ak["required_time_constraints"]
            del ak["required_time_constraints"]
        if not "time_constraints" in ak:
            ak["time_constraints"] = []
        if not "room_constraints" in ak:
            ak["room_constraints"] = []

        if "duration" not in ak:
            if "duration" in ak["info"]:
                ak["duration"] = int(ak["info"]["duration"])
                del ak["info"]["duration"]
            else:
                ak["duration"] = default_duration
                print(f"Setting default duration for AK {ak['info']['name']}")
        else:
            ak["duration"] = int(ak["duration"])

    write_ak_data(poll_name, data)


def clean_participants(poll_name: str) -> None:
    for result_json in get_export_dir(poll_name).glob("*.json"):
        with result_json.open("r") as ff:
            result_dict = json.load(ff)

        if "required_time_constraints" in result_dict.keys():
            result_dict["time_constraints"] = result_dict["required_time_constraints"]
            del result_dict["required_time_constraints"]

        if not "room_constraints" in result_dict:
            result_dict["room_constraints"] = []

        with result_json.open("w") as ff:
            json.dump(result_dict, ff, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    fire.Fire(
        {
            "data": clean_data,
            "participants": clean_participants,
        }
    )
