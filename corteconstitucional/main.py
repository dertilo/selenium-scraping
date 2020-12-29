from util import data_io

from corteconstitucional.build_csv import build_dataframe, NO_EDICTO, ANO
from corteconstitucional.corteconstitucional_edictos import download_edictos
from corteconstitucional.corteconstitucional_procesos import scrape_proceso_tables, \
    download_proceso_data
from corteconstitucional.merge_edictos_proceso_tables import \
    merge_edictos_proceso_tables
from corteconstitucional.parse_edictos import parse_edictos, Edicto


def main():
    download_edictos()
    print("PARSE EDICTOS")
    edictos = parse_edictos()
    # edictos = [Edicto(**d) for d in data_io.read_jsonl("edictos.jsonl")]
    print("DOWNLOAD PROCESO TABLES")
    download_proceso_data(edictos)
    print("MERGE DATA")
    merged_data = merge_edictos_proceso_tables(edictos)
    df = build_dataframe(merged_data)
    df = df.sort_values([ANO, NO_EDICTO], ascending=[True, True])
    consecutive_edicto_no_step = df[df[NO_EDICTO].diff() > 1]
    for _, d in consecutive_edicto_no_step.iterrows():
        print(f"year: {d[ANO]}; no: {d[NO_EDICTO] - 1}")
    df.to_csv("tilo_table.csv", sep="\t", index=False)


if __name__ == '__main__':
    main()
