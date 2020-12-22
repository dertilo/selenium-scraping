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
ACTUACION_SECRETARIA = "Actuación Secretaría"


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
        d[ACTUACION_SECRETARIA] = parse_date(d[ACTUACION_SECRETARIA])

    return TableDatum(
        raw_datum["id"],# actually expediente
        data,
    )

def edicto_id(e:Edicto):
    return f"{e.source}_{e.no}"

if __name__ == "__main__":
    assert False # see merge_edictos_proceso_tables.py

