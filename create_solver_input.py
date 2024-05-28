import json
from pathlib import Path
from typing import Iterable

import fire

from wsgi import get_export_dir, read_ak_data


def construct_solver_json(
    poll_name: str,
    output_path: str = "export.json",
    default_duration: int = 2,
    fixed_preferences: Iterable[dict] | None = None,
) -> dict:
    data = read_ak_data(poll_name)

    for idx, ak in enumerate(data["aks"]):
        if "id" not in ak:
            ak["id"] = f"ak{idx}"
        ak["properties"] = {}

    participants = []
    for result_json in get_export_dir(poll_name).glob("*.json"):
        with result_json.open("r") as ff:
            result_dict = json.load(ff)
        result_dict["id"] = result_json.stem
        if fixed_preferences:
            result_dict["preferences"].extend(fixed_preferences)
        participants.append(result_dict)

    data["participants"] = participants

    with Path(output_path).open("w") as ff:
        json.dump(data, ff, indent=2, ensure_ascii=False)

    return data


if __name__ == "__main__":
    fire.Fire(construct_solver_json)
