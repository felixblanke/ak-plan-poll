import fire
import pandas as pd

from wsgi import write_ak_data


def df_to_ak_list(df: pd.DataFrame) -> list[dict]:
    return [
        {
            "info": {
                "name": row["AK"],
                "description": row["AKS Kurzbeschreibung"],
                "head": "" if pd.isna(row["Leitung"]) else row["Leitung"],
                "reso": "Reso" in row["AKS Typ"].split(","),
            }
        }
        for ak_idx, row in df.iterrows()
    ]


def convert_wiki_csv(wiki_csv_file: str = "result.csv", poll_name: str = "koma-draft"):
    # download csv from wiki export
    df = pd.read_csv(wiki_csv_file)
    ak_list = df_to_ak_list(df)

    write_ak_data(poll_name=poll_name, data={"aks": ak_list})


if __name__ == "__main__":
    fire.Fire(convert_wiki_csv)
