from collections import Counter, defaultdict
from pprint import pprint

import pandas as pd
from util import data_io


def to_datetime(df, key):
    df[key] = pd.to_datetime(df[key])


def load_tati_data():
    """
    this data was collected manually by juan and tatiana
    slightly cleaned original file: 'Datos informe cc - Gráficos con ajuste fila 396 Tata cleaned-by-tilo.ods'
    """
    df = pd.read_csv(
        "/home/tilo/code/DATA/visualizations-for-tatiana/sentencias_constitucionales_fechas.csv",
        sep="\t",
    )
    # pprint(df.head())
    fecha_radicacion = "Fecha Radicación"
    fecha_decision = "Fecha Decisión"
    fijacion_edicto = "Fijación Edicto "  # WTF there is a space!
    for k in [fecha_decision, fecha_radicacion, fijacion_edicto]:
        to_datetime(df, k)

    return df


def get_key_from_tati_data(d):
    try:
        key = f"{int(d['Año'])}_{int(d['Nro. Edicto'])}"
    except Exception:
        key = None
    return key

def normalize_expediente(e):
    tupe, number = e.split("-")
    while number.startswith("0"):
        number = number[1:]
    return f"{tupe}-{number}"

if __name__ == "__main__":
    g = data_io.read_jsonl("/tmp/merged_edictos2tables.jsonl")
    data = list(g)
    # print(Counter(len(d["tables"]) for d in g))
    df = load_tati_data()
    tati_data = df.to_dict("records")
    key2tati_data = {
        get_key_from_tati_data(d): d
        for d in tati_data
        if get_key_from_tati_data(d) is not None
    }
    shit_counter = 0
    for d in data:
        year = d["edicto_year"]
        num = int(d["no"])
        key = f"{year}_{num}"
        if key in key2tati_data.keys():
            tati_datum = key2tati_data.pop(key)
            exps = [f"{tati_datum['Proceso']}-{tati_datum['Expediente']}"]
            if "y" in exps[0]:
                exps = exps[0].split(" y ")
                exps[1]=exps[0][0]+"-"+exps[1]
            if any(exp not in [normalize_expediente(e) for e in d["expedientes"]] for exp in exps):
                print(exps)

                x = d.pop("tables")
                pprint(d)
                pprint(tati_datum)
                shit_counter +=1

    print(shit_counter)
