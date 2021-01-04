import pandas as pd
from typing import List, Dict

from corteconstitucional.compare_data import to_datetime

ANO = "Año"
NO_EDICTO = "Nro. Edicto"

FECHA_RADICACION = "Fecha Radicación"
FECHA_DECISION = "Fecha Decisión"
FIJACION_EDICTO = "Fijación Edicto"

fijacion = "Fallo.Fijación Edicto"
aprobacion = "Fallo.Aprobación Proyecto"
radicacion = "Radicación"
ACUMULADA = "Acumulada"

def load_csv_data(file: str = "tati_table.csv") -> List[Dict]:
    df = pd.read_csv(file, sep="\t")
    for k in [FECHA_DECISION, FECHA_RADICACION, FIJACION_EDICTO]:
        to_datetime(df, k)

    data = df.to_dict("records")
    return data


