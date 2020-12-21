from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime

import regex
from typing import List
from pathlib import Path

import os
import pandas
from tqdm import tqdm
from util import data_io

from corteconstitucional.parse_edictos import generate_edictos, Edicto


@dataclass(frozen=True, eq=True)
class TableDatum:
    expediente: str
    fechas:List[str]


month_pattern = regex.compile(r"[A-Za-z]{1,4}")


def parse_date(s: str):
    month = month_pattern.search(s).group()
    map = {"Abr": "Apr", "Ago": "Aug", "Dic": "Dec", "Ene": "Jan"}
    mapped_month = map.get(month, month)
    normalized_date_s = s.replace(month, mapped_month)
    date = datetime.strptime(normalized_date_s, "%b %d %Y")
    assert date.day >= 1
    assert date.month >= 1
    return date.strftime("%m/%d/%Y")


def build_table_datum(raw_datum):
    html = raw_datum["html"]
    dfs = pandas.read_html(html)
    assert len(dfs) <= 2
    table_df = dfs[1] if len(dfs) == 2 else dfs[0]
    assert table_df.columns.size == 2
    table_df.columns = table_df.iloc[0]
    table_df = table_df[1:]
    data = table_df.to_dict("records")

    for d in data:
        d["Actuación Secretaría"] = parse_date(d["Actuación Secretaría"])

    return TableDatum(
        raw_datum["id"],# actually expediente
        data,
    )

def edicto_id(e:Edicto):
    return f"{e.source}_{e.no}"

if __name__ == "__main__":
    # edictos_file = f"{os.environ['HOME']}/data/corteconstitucional/edictos/documents.jsonl"
    # edictos = {d:d for d in data_io.read_jsonl(edictos_file)}
    print("edictos")
    edictos: List[Edicto] = list(tqdm(generate_edictos()))
    print(f"unique edictos {len(set(edictos))}")
    exp2edicto = {exp: e for e in edictos for exp in e.expedientes}
    print("procesos")
    data_path = f"{os.environ['HOME']}/data/corteconstitucional/procesos_tables"
    raw_data = (
        data_io.read_json(str(file)) for file in tqdm(Path(data_path).glob("*.json"))
    )
    table_data = [build_table_datum(d) for d in raw_data]
    notfound_expedientes = [
        t.expediente for t in table_data if t.expediente not in exp2edicto.keys()
    ]
    print(f"cound not find {len(notfound_expedientes)} expedientes")
    data_io.write_lines("/tmp/notfound_expedientes.txt", notfound_expedientes)
    data_io.write_jsonl(
        "/tmp/merge.jsonl",
        (
            {**asdict(t), **asdict(exp2edicto[t.expediente])}
            for t in table_data
            if t.expediente not in notfound_expedientes
        ),
    )

"""
edictos
2231it [00:28, 79.07it/s]
0it [00:00, ?it/s]unique edictos 2224
procesos
2396it [00:11, 199.94it/s]
cound not find 0 expedientes
"""