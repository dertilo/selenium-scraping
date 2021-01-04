import os
from collections import defaultdict

import pandas
from datetime import datetime
from pandas.core.frame import DataFrame
from typing import Dict, Generator, List
from util import data_io
from util.util_methods import merge_dicts

from corteconstitucional.common import FIJACION_EDICTO, FECHA_DECISION, \
    FECHA_RADICACION, fijacion, aprobacion, radicacion, ACUMULADA, ANO, NO_EDICTO
from corteconstitucional.parse_edictos import reformat_date
from corteconstitucional.parse_proceso_tables import ACTUACION_SECRETARIA
from corteconstitucional.regexes import MESES_ESP


def fix_sentencia(s:str)->str:
    s = s.replace(" ","")
    assert s.startswith("C")
    if s[1]!="-":
        s = "C-"+s[1:]
    return s

def manual_patch(d):
    if all([d[k]==v for k,v in [(ANO,2019),("Expediente",12355), (NO_EDICTO,31)]]):
        d["Sentencia"] = 'C-046A/19'
        print("fixed!")
    return d

def flatten_expedientes(d:Dict)->Generator:
    tables = d.pop("tables")
    exp2fechas = {t["expediente"]:t["fechas"] for t in tables }
    for exp, fechas in exp2fechas.items():
        dd = defaultdict(list)
        for f in fechas:
            etapa = f["Etapa"]
            if etapa in [fijacion, aprobacion, radicacion, ACUMULADA]:
                actuacion = f[ACTUACION_SECRETARIA]
                dd[etapa].append(actuacion)
        dd[radicacion] = dd[radicacion][0]

        datum = merge_dicts([d, dd, {"expediente": exp}])
        edicto_date = datetime.strptime(datum["edicto_date"], "%m/%d/%Y")
        year = int(datum["edicto_year"])
        mes_name = MESES_ESP[edicto_date.month-1].capitalize()
        proceso,expediente = datum["expediente"].split("-")


        tati_datum = {
            ANO:year,
            "Mes": mes_name,
            NO_EDICTO: datum["no"],
            "Proceso": proceso ,
            "Expediente":int(expediente),
            "Sentencia": fix_sentencia(datum["sentencia"]),
            FECHA_RADICACION:reformat_date(datum[radicacion]),
            FECHA_DECISION:datum["sentencia_date"],
            FIJACION_EDICTO: reformat_date(datum["edicto_date"]),
            ACUMULADA: datum[ACUMULADA][0] if ACUMULADA in datum else None
        }
        yield tati_datum


def build_dataframe(merged_data:List)->DataFrame:
    rows = (manual_patch(r) for d in merged_data
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
    df.to_csv(f"tilo_table.csv",sep="\t",index=False)

