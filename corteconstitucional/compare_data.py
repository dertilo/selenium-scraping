import os
from collections import defaultdict

import Levenshtein
import numpy
import pandas as pd
from pprint import pprint
from tqdm import tqdm

from util import data_io

from corteconstitucional.build_csv import fix_sentencia
from corteconstitucional.regexes import MESES_ESP


def same_sentencia_code(a, b):
    return fix_sentencia(a) == fix_sentencia(b)


ANO = "Año"
NO_EDICTO = "Nro. Edicto"


def build_id(d):

    try:
        proceso = d["Proceso"]
        assert isinstance(proceso, str)
        eid = f"{int(d[ANO])}-{int(d[NO_EDICTO])}-{proceso}-{int(d['Expediente'])}"
    except Exception:
        eid = None
    return eid


def to_datetime(df, key):
    df[key] = pd.to_datetime(df[key])


def load_csv_data(file="tati_table.csv"):
    df = pd.read_csv(file, sep="\t")
    fecha_radicacion = "Fecha Radicación"
    fecha_decision = "Fecha Decisión"
    fijacion_edicto = "Fijación Edicto"  # WTF there is a space!
    for k in [fecha_decision, fecha_radicacion, fijacion_edicto]:
        to_datetime(df, k)

    data = df.to_dict("records")
    return data


def find_tilo_in_tati():
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


def normalize_datum(d):
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
            "Fecha Radicación": d["Fecha Radicación"].strftime("%d/%m/%Y"),
            "Fecha Decisión": d["Fecha Decisión"].strftime("%d/%m/%Y"),
            "Fijación Edicto": d["Fijación Edicto"].strftime("%d/%m/%Y"),
        }
    except Exception:
        datum = None
    return datum


def compare_data():
    global tati_data, tilo_data
    base_dir = "corteconstitucional"

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
    distances = calc_distances(tati_data, tilo_data)
    mapping = []
    for i, tilo in tqdm(enumerate(tilo_data)):
        kk, dist = min(
            [(int(ii), d) for ii, d in distances[str(i)].items()], key=lambda x: x[1]
        )
        mapped = {"tilo": tilo, "dist": dist}
        if dist < 10:
            mapped["tati"] = tati_data[kk]
        mapping.append(mapped)

    def build_line(d, k):
        return "\t".join([str(x) for x in d.get(k, {}).values()])

    # data_io.write_jsonl("/tmp/mapping.jsonl",mapping)
    data_io.write_lines(f"{base_dir}/tilo_mapped.csv", [build_line(m, "tilo") for m in mapping])
    data_io.write_lines(f"{base_dir}/tati_mapped.csv", (build_line(m, "tati") for m in mapping))
    # pd.DataFrame([m["tilo"] for m in mapping]).to_csv(f"tilo_mapped.csv",sep="\t")
    # pd.DataFrame([m.get("tati",{}) for m in mapping]).to_csv(f"tati_mapped.csv",sep="\t")
    # data_io.write_jsonl("tilo.jsonl",[m["tilo"] for m in mapping])
    # data_io.write_jsonl("tati.jsonl",[m.get("tati",{}) for m in mapping])
    # find_tilo_in_tati()


def calc_distances(tati_data, tilo_data):
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