from collections import defaultdict, Counter
from pprint import pprint

import pandas
from util import data_io

from corteconstitucional.parse_proceso_tables import ACTUACION_SECRETARIA

fijacion = "Fallo.Fijación Edicto"
aprobacion = "Fallo.Aprobación Proyecto"
radicacion = "Radicación"

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
        if all([k in dd for k in [fijacion,aprobacion,radicacion]]):
            yield {**d,**dd,**{"expediente":exp}}


def build_dataframe(merged_data):
    rows = (r for d in merged_data
            for r in flatten_expedientes(d))
    # pprint(Counter(f"{r['no']}_{r['edicto_year']}" for r in rows))
    df = pandas.DataFrame(rows)
    return df


if __name__ == '__main__':
    merged_data = list(data_io.read_jsonl("/tmp/merged_edictos2tables.jsonl"))

    df = build_dataframe(merged_data)
    df.to_csv("/tmp/table.csv",sep="\t")
