from pathlib import Path

import os
import pandas
from tqdm import tqdm
from util import data_io

if __name__ == '__main__':
    data_path = f"{os.environ['HOME']}/data/corteconstitucional/procesos_tables"
    for file in tqdm(Path(data_path).glob("*.json")):
        d = data_io.read_json(str(file))
        html = d["html"]
        dfs = pandas.read_html(html)
        assert len(dfs)<=2
        table_df = dfs[1] if len(dfs)==2 else dfs[0]
        assert table_df.columns.size == 2
        dfd = table_df.to_dict()
        datum = {k:dfd[1][i] for i,k in dfd[0].items()}