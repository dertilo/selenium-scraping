from collections import defaultdict
from datetime import datetime

from typing import Tuple
from typing import Union

import Levenshtein
import os
from pprint import pprint
from tqdm import tqdm
from typing import Dict, List, Any
from util import data_io

from corteconstitucional.build_csv import fix_sentencia
from corteconstitucional.common import ANO, NO_EDICTO, load_csv_data, FIJACION_EDICTO, \
    FECHA_DECISION, FECHA_RADICACION, PROCESO, EXPEDIENTE
from corteconstitucional.regexes import MESES_ESP


def same_sentencia_code(a, b):
    return fix_sentencia(a) == fix_sentencia(b)


def build_id(d):

    try:
        proceso = d[PROCESO]
        assert isinstance(proceso, str)
        eid = f"{int(d[ANO])}-{int(d[NO_EDICTO])}-{proceso}-{int(d[EXPEDIENTE])}"
    except Exception:
        eid = None
    return eid


def find_tilo_in_tati(tilo_data, tati_data):
    eid2tilo = {build_id(d): d for d in tilo_data}
    assert not any([k is None for k in eid2tilo.keys()])
    shit_counter = 0
    for d in tqdm(tati_data):
        eid = build_id(d)
        if eid is None:
            print(f"invalid id: {d}")
            continue
        if eid not in eid2tilo.keys():
            print("NOT EXISTENT!")
            print(d)
            shit_counter += 1
        else:
            tilo_d = eid2tilo[eid]
            if not same_sentencia_code(d["Sentencia"], tilo_d["Sentencia"]):
                shit_counter += 1
                print("DIFFERING")
                pprint(d)
                pprint(tilo_d)
    print(f"shit_counter: {shit_counter}")
    """
    shit_counter: 4
    """

def reformat_date(date:str)->str:
    try:
        return datetime.strftime(datetime.strptime(date, "%d/%m/%Y"), "%d/%m/%Y")
    except Exception:
        return datetime.strftime(datetime.strptime(date, "%d/%m/%y"), "%d/%m/%Y")

def normalize_datum(d: Dict[str, Any]) -> Union[None, Dict[str, Any]]:
    try:
        year = int(d[ANO])
        assert year <= 2021 and year > 1990
        month_name = d["Mes"]
        assert month_name.lower() in MESES_ESP
        no_edicto = int(d[NO_EDICTO])
        proceso = d["Proceso"]
        assert isinstance(proceso, str)
        datum = {
            ANO: year,
            "Mes": month_name,
            NO_EDICTO: no_edicto,
            "Proceso": proceso,
            "Expediente": int(d["Expediente"]),
            "Sentencia": fix_sentencia(d["Sentencia"]),
            FECHA_RADICACION: reformat_date(d["Fecha Radicación"]),
            FECHA_DECISION: reformat_date(d["Fecha Decisión"]),
            FIJACION_EDICTO: reformat_date(d["Fijación Edicto"]),
        }
    except Exception:
        datum = None
    return datum


def compare_data():
    base_dir = "corteconstitucional"
    tati_data, tilo_data = read_data(base_dir)
    distances = calc_distances(tati_data, tilo_data)

    mapping = build_mapping(distances, tati_data, tilo_data)

    dump_mappings(base_dir, mapping)


def read_data(base_dir: str) -> Tuple[List, List]:
    raw_tati_data = load_csv_data(f"{base_dir}/tati_table.csv")
    tati_data = list(
        filter(lambda x: x is not None, map(normalize_datum, raw_tati_data))
    )
    print(f"tati-data: {len(tati_data)} of {len(raw_tati_data)} are valid")
    raw_tilo_data = load_csv_data(f"{base_dir}/tilo_table.csv")
    tilo_data = list(
        filter(lambda x: x is not None, map(normalize_datum, raw_tilo_data))
    )
    print(f"tilo-data: {len(tilo_data)} of {len(raw_tilo_data)} are valid")
    return tati_data, tilo_data


def build_mapping(
    distances: Dict[str, Dict], tati_data: List[Dict], tilo_data: List[Dict]
) -> List[Dict]:
    mapping = []
    for i, tilo in tqdm(enumerate(tilo_data)):
        kk, dist = min(
            [(int(ii), d) for ii, d in distances[str(i)].items()], key=lambda x: x[1]
        )
        mapped = {"tilo": tilo, "dist": dist}
        if dist < 10:
            mapped["tati"] = tati_data[kk]
        mapping.append(mapped)
    return mapping


def dump_mappings(base_dir: str, mapping: List[Dict]):
    def build_line(d: Dict[str, Any], k: str) -> str:
        return "\t".join([str(x) for x in d.get(k, {}).values()])

    data_io.write_lines(
        f"{base_dir}/tilo_mapped.csv", [build_line(m, "tilo") for m in mapping]
    )
    data_io.write_lines(
        f"{base_dir}/tati_mapped.csv", (build_line(m, "tati") for m in mapping)
    )


def calc_distances(tati_data: List[Dict], tilo_data: List[Dict]) -> Dict[str, Dict]:
    distances = defaultdict(dict)
    distances_json = "/tmp/distances.json"
    if not os.path.isfile(distances_json):
        for i, tilo in tqdm(enumerate(tilo_data)):
            for ii, tati in enumerate(tati_data):
                distances[str(i)][str(ii)] = Levenshtein.distance(str(tilo), str(tati))
        data_io.write_json(distances_json, distances)
    else:
        distances = data_io.read_json(distances_json)
    return distances


if __name__ == "__main__":
    compare_data()
    # base_dir = "corteconstitucional"
    # tati_data, tilo_data = read_data(base_dir)
    # distances = calc_distances(tati_data, tilo_data)
    #
    # mapping = build_mapping(distances, tati_data, tilo_data)
