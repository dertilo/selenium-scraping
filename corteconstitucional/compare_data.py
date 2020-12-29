import pandas as pd
from pprint import pprint
from tqdm import tqdm

from util import data_io


def same_sentencia_code(a,b):
    return before_slash(a) == before_slash(b)

def before_slash(a):
    return a.split("/")[0] if "/" in a else a


ANO = "Año"
NO_EDICTO = "Nro. Edicto"

def try_int(x):
    try:
        return int(x)
    except Exception:
        return -1

def build_id(d):

    return f"{try_int(d[ANO])}-{try_int(d[NO_EDICTO])}-{d['Proceso']}-{try_int(d['Expediente'])}"


def to_datetime(df,key):
    df[key] = pd.to_datetime(df[key])


def load_csv_data(
        file="tati_table.csv"
):
    df = pd.read_csv(file, sep="\t")
    fecha_radicacion = "Fecha Radicación"
    fecha_decision = "Fecha Decisión"
    fijacion_edicto = "Fijación Edicto"  # WTF there is a space!
    for k in [fecha_decision, fecha_radicacion, fijacion_edicto]:
        to_datetime(df, k)

    data = df.to_dict('records')
    return data


def find_tilo_in_tati():
    exp2datum_tilo = {build_id(d): d for d in tilo_data}
    shit_counter = 0
    for d in tqdm(tati_data):
        eid = build_id(d)
        if eid not in exp2datum_tilo.keys():
            print("NOT EXISTENT!")
            print(d)
            shit_counter += 1
        else:
            tilo_d = exp2datum_tilo[eid]
            if not same_sentencia_code(d["Sentencia"], tilo_d["Sentencia"]):
                shit_counter += 1
                print("DIFFERING")
                pprint(d)
                pprint(tilo_d)
    print(f"shit_counter: {shit_counter}")
    """
    shit_counter: 17
    """


if __name__ == '__main__':
    tati_data = load_csv_data("tati_table.csv")
    tilo_data = load_csv_data("tilo_table.csv")

    find_tilo_in_tati()