from corteconstitucional.build_csv import build_dataframe
from corteconstitucional.corteconstitucional_edictos import download_edictos
from corteconstitucional.corteconstitucional_procesos import scrape_proceso_tables, \
    download_proceso_data
from corteconstitucional.merge_edictos_proceso_tables import \
    merge_edictos_proceso_tables
from corteconstitucional.parse_edictos import parse_edictos

if __name__ == '__main__':
    download_edictos()
    print("PARSE EDICTOS")
    edictos = parse_edictos()
    print("DOWNLOAD PROCESO TABLES")
    download_proceso_data(edictos)
    print("MERGE DATA")
    merged_data = merge_edictos_proceso_tables(edictos)

    df = build_dataframe(merged_data)
    df.to_csv("/tmp/table.csv",sep="\t")
