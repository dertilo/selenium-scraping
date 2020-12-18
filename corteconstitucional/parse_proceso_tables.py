from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime

import regex
from typing import List

from pprint import pprint

from pathlib import Path

import os
import pandas
from tqdm import tqdm
from util import data_io

from corteconstitucional.parse_edictos import generate_edictos, Edicto


@dataclass(frozen=True, eq=True)
class TableDatum:
    expediente: str
    fijacion: str
    radicacion: str
    aprobacion: str


month_pattern = regex.compile(r"[A-Za-z]{1,4}")

def parse_date(s: str):
    month = month_pattern.search(s).group()
    map = {"Abr": "Apr", "Ago": "Aug", "Dic": "Dec", "Ene": "Jan"}
    mapped_month = map.get(month, month)
    normalized_date_s = s.replace(month, mapped_month)
    date = datetime.strptime(normalized_date_s, "%b %d %Y")
    return date.strftime("%m/%d/%Y")


def build_table_datum(d):
    html = d["html"]
    dfs = pandas.read_html(html)
    assert len(dfs) <= 2
    table_df = dfs[1] if len(dfs) == 2 else dfs[0]
    assert table_df.columns.size == 2
    dfd = table_df.to_dict()
    kv = {k: dfd[1][i] for i, k in dfd[0].items()}
    fijacion = kv.get("Fallo.Fijación Edicto", None)
    aprobacion = kv.get("Fallo.Aprobación Proyecto", None)
    radicacion = kv.get("Radicación")
    return TableDatum(
        d["id"],
        *[
            parse_date(s) if s is not None else None
            for s in [fijacion, aprobacion, radicacion]
        ],
    )


if __name__ == "__main__":
    # edictos_file = f"{os.environ['HOME']}/data/corteconstitucional/edictos/documents.jsonl"
    # edictos = {d:d for d in data_io.read_jsonl(edictos_file)}
    edictos: List[Edicto] = list(tqdm(generate_edictos()))
    exp2edicto = {exp: e for e in edictos for exp in e.expedientes}
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
