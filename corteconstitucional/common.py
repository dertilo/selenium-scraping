import pandas as pd
from pandas import DataFrame
from typing import List, Dict

ANO = "Año"
NO_EDICTO = "Nro. Edicto"

FECHA_RADICACION = "Fecha Radicación"
FECHA_DECISION = "Fecha Decisión"
FIJACION_EDICTO = "Fijación Edicto"
PROCESO = 'Proceso'
EXPEDIENTE = 'Expediente'

fijacion = "Fallo.Fijación Edicto"
aprobacion = "Fallo.Aprobación Proyecto"
radicacion = "Radicación"
ACUMULADA = "Acumulada"

def load_csv_data(file: str = "tati_table.csv") -> List[Dict]:
    df = pd.read_csv(file, sep="\t")
    data = df.to_dict("records")
    return data


def to_datetime(df: DataFrame, key: str):
    df[key] = pd.to_datetime(df[key],dayfirst=False)