import os
from bs4 import BeautifulSoup
from tqdm import tqdm

from typing import Iterable, Dict, Any
from util import data_io

from corteconstitucional.common import FECHA_RADICACION, PROCESO, EXPEDIENTE
from corteconstitucional.compare_data import build_mapping, calc_distances, read_data
from corteconstitucional.corteconstitucional_procesos import (
    fire_search,
    FIRST_ROW_POPUP,
    POPUP_REFRESH_BUTTON,
)
from selenium_util import build_chrome_driver, click_it


def take_proceso_table_screenshots(diffs: Iterable):
    base_url = "https://www.corteconstitucional.gov.co/secretaria/"
    data_path = (
        f"{os.environ['HOME']}/data/corteconstitucional/procesos_tables/screenshots"
    )
    os.makedirs(data_path, exist_ok=True)
    download_path = f"{data_path}/downloads"
    wd = build_chrome_driver(download_path, headless=True)

    for d in tqdm(diffs):
        search_id = f"{d['tilo'][PROCESO]}-{d['tilo'][EXPEDIENTE]}"
        try:
            fire_search(base_url, search_id, wd)
            name = prepare_for_screenshot(wd)
            png_file = f"{data_path}/{search_id}.png"
            wd.save_screenshot(png_file)
            yield d, png_file
        except BaseException as e:
            print(f"{search_id} fucked it up!")
            yield d, None


def prepare_for_screenshot(wd):
    click_it(wd, FIRST_ROW_POPUP)
    wd.switch_to.frame(0)
    click_it(wd, POPUP_REFRESH_BUTTON)
    # wd.switch_to.frame(0)
    html = wd.page_source
    soup = BeautifulSoup(html, features="html.parser")
    # df = pandas.read_html(html)[0]
    title = soup.find_all("title")[0].text
    assert "Proceso" in title
    name = "-".join([s for s in title.split(" ") if len(s) > 0])
    return name


def build_line(d: Dict[str, Any], k: str) -> str:
    return " | ".join([str(x) for x in d.get(k, {}).values()])


def generate_markdown_sections(diffs):

    for d, png_file in take_proceso_table_screenshots(diffs):
        colnames, tilo_values = list(zip(*[(k, str(v)) for k, v in d["tilo"].items()]))
        tati_values = [str(d["tati"][k]) for k in colnames]
        header = " | ".join(colnames)
        line = " | ".join(["---" for _ in colnames])
        tilo_row = " | ".join(tilo_values)
        tati_row = " | ".join(tati_values)
        eid = f"{d['tilo'][PROCESO]}-{d['tilo'][EXPEDIENTE]}"
        markdown = (
            f"\n### {eid} different {FECHA_RADICACION}\n"
            f"{header}\n"
            f"{line}\n"
            f"{tilo_row}\n"
            f"{tati_row}\n"
            f"![image-eid]({png_file})"
        )
        yield markdown


if __name__ == "__main__":

    base_dir = "corteconstitucional"
    tati_data, tilo_data = read_data(base_dir)
    distances = calc_distances(tati_data, tilo_data)

    diffs = list(
        filter(lambda m: m["dist"] > 0, build_mapping(distances, tati_data, tilo_data))
    )

    diff_radicacion = [
        d
        for d in diffs
        if "tati" in d and d["tilo"][FECHA_RADICACION] != d["tati"][FECHA_RADICACION]
    ]

    for s in generate_markdown_sections(diff_radicacion[:3]):
        data_io.write_file("differences.md", s, mode="ab")
