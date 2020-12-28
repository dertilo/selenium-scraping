from collections import defaultdict, Counter
from datetime import datetime

from pprint import pprint

import pandas
from util import data_io

from corteconstitucional.parse_edictos import reformat_date
from corteconstitucional.parse_proceso_tables import ACTUACION_SECRETARIA
from corteconstitucional.regexes import MESES, MESES_ESP

fijacion = "Fallo.Fijación Edicto"
aprobacion = "Fallo.Aprobación Proyecto"
radicacion = "Radicación"

ANO = "Año"
NO_EDICTO = "Nro. Edicto"
def no_leading_zeros(s):
    while s.startswith("0"):
        s = s[1:]
    return s

def flatten_expedientes(d):
    tables = d.pop("tables")
    exp2fechas = {t["expediente"]:t["fechas"] for t in tables }
    for exp, fechas in exp2fechas.items():
        dd = defaultdict(list)
        for f in fechas:
            etapa = f["Etapa"]
            if etapa in [fijacion,aprobacion,radicacion]:
                actuacion = f[ACTUACION_SECRETARIA]
                dd[etapa].append(actuacion)
        dd[radicacion] = dd[radicacion][0]

        datum = {**d, **dd, **{"expediente": exp}}
        edicto_date = datetime.strptime(datum["edicto_date"], "%m/%d/%Y")
        year = int(datum["edicto_year"])
        mes_name = MESES_ESP[edicto_date.month-1].capitalize()
        proceso,expediente = datum["expediente"].split("-")

        tati_datum = {
            ANO:year,
            "Mes": mes_name,
            NO_EDICTO: datum["no"],
            "Proceso": proceso ,
            "Expediente":no_leading_zeros(expediente),
            "Sentencia": datum["sentencia"],
            "Fecha Radicación":reformat_date(datum[radicacion]),
            "Fecha Decisión":datum["sentencia_date"],
            "Fijación Edicto": reformat_date(datum["edicto_date"]),

        }
        yield tati_datum


def build_dataframe(merged_data):
    rows = (r for d in merged_data
            for r in flatten_expedientes(d)
            if r[ANO]>=2015)
    # pprint(Counter(f"{r['no']}_{r['edicto_year']}" for r in rows))
    df = pandas.DataFrame(rows)
    return df


if __name__ == '__main__':
    merged_data = list(data_io.read_jsonl("/tmp/merged_edictos2tables.jsonl"))
    df = build_dataframe(merged_data)
    df = df.sort_values([ANO, NO_EDICTO], ascending=[True, True])
    consecutive_edicto_no_step = df[df[NO_EDICTO].diff() > 1]
    for _,d in consecutive_edicto_no_step.iterrows():
        print(f"year: {d[ANO]}; no: {d[NO_EDICTO]-1}")
    df.to_csv("tilo_table.csv",sep="\t",index=False)
