from collections import Counter, defaultdict
from pprint import pprint

import pandas as pd
from util import data_io

def to_datetime(df,key):
    df[key] = pd.to_datetime(df[key])

def load_tati_data():
    """
    this data was collected manually by juan and tatiana
    slightly cleaned original file: 'Datos informe cc - Gráficos con ajuste fila 396 Tata cleaned-by-tilo.ods'
    """
    df = pd.read_csv("/home/tilo/code/DATA/visualizations-for-tatiana/sentencias_constitucionales_fechas.csv", sep="\t")
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

if __name__ == '__main__':
    g = data_io.read_jsonl("/tmp/merged_edictos2tables.jsonl")
    data = list(g)
    # print(Counter(len(d["tables"]) for d in g))
    dd = defaultdict(dict)
    for d in data:
        year = int(d["edicto_date"].split("/")[-1])
        dd[year][int(d["no"])] = d
    df = load_tati_data()
    tati_data = df.to_dict('records')
    key2tati_data = {get_key_from_tati_data(d):d for d in tati_data if get_key_from_tati_data(d) is not None}
    shit_counter=0
    for d in data:
        year = d["edicto_year"]
        num = int(d["no"])
        key = f"{year}_{num}"
        if key in key2tati_data.keys():
            tati_datum = key2tati_data.pop(key)
        else:
            shit_counter +=1

    print(len(key2tati_data))
    pprint(key2tati_data)