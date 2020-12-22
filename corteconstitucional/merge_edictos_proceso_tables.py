from dataclasses import asdict

import os

from pathlib import Path
from tqdm import tqdm

from util import data_io

from corteconstitucional.parse_edictos import Edicto
from corteconstitucional.parse_proceso_tables import build_table_datum


def merge_edictos_proceso_tables(
        edictos,
        data_path=f"{os.environ['HOME']}/data/corteconstitucional/procesos_tables"
    ):
    raw_data = list(
        data_io.read_json(str(file)) for file in tqdm(Path(data_path).glob("*.json"))
    )
    table_data = (build_table_datum(d) for d in raw_data)
    exp2table = {t.expediente: t for t in table_data}
    g = (
        {**asdict(e), **{"tables": [asdict(exp2table[exp]) for exp in e.expedientes]}}
        for e in edictos
    )
    merged_data = list(g)
    return merged_data


if __name__ == "__main__":
    edictos = [Edicto(**d) for d in data_io.read_jsonl("edictos.jsonl")]
    merged_data = merge_edictos_proceso_tables(edictos)
    data_io.write_jsonl("/tmp/merged_edictos2tables.jsonl", merged_data)
