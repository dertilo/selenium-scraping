import os
from bs4 import BeautifulSoup
from tqdm import tqdm

from typing import Iterable, Dict, Any
from util import data_io

from corteconstitucional.common import FECHA_RADICACION, PROCESO, EXPEDIENTE
from corteconstitucional.compare_data import (
    build_mapping,
    calc_distances,
    read_data,
    build_id,
)
from corteconstitucional.corteconstitucional_procesos import (
    fire_search,
    FIRST_ROW_POPUP,
    POPUP_REFRESH_BUTTON,
)
from selenium_util import build_chrome_driver, click_it


def take_proceso_table_screenshots(diffs: Iterable):
    base_url = "https://www.corteconstitucional.gov.co/secretaria/"
    os.makedirs(data_path, exist_ok=True)
    download_path = f"{data_path}/downloads"
    wd = build_chrome_driver(download_path, headless=True, window_size=(1080, 1080))

    for d in tqdm(diffs):
        search_id = f"{d['tilo'][PROCESO]}-{d['tilo'][EXPEDIENTE]}"
        try:
            png_file = f"{data_path}/{search_id}.png"
            if not os.path.isfile(png_file):
                print(f"screen-shotting: {search_id}")
                fire_search(base_url, search_id, wd)
                prepare_for_screenshot(wd)
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
    def format_string(s, key):
        if key == FECHA_RADICACION:
            s = f"__{s}__"
        else:
            pass
        return s

    for d, png_file in take_proceso_table_screenshots(diffs):
        colnames, tilo_values = [
            list(x)
            for x in zip(*[(k, format_string(str(v), k)) for k, v in d["tilo"].items()])
        ]

        colnames.insert(0, "source")
        tilo_values.insert(0, "tilo")

        tati_values = ["juan/tati"] + [
            format_string(str(d["tati"][k]), k) for k in colnames[1:]
        ]
        header = " | ".join(colnames)
        line = " | ".join(["---" for _ in colnames])
        tilo_row = " | ".join(tilo_values)
        tati_row = " | ".join(tati_values)
        eid = f"{d['tilo'][PROCESO]}-{d['tilo'][EXPEDIENTE]}"
        markdown = (
            f"\n### {eid} different: {FECHA_RADICACION}\n"
            f"{header}\n"
            f"{line}\n"
            f"{tilo_row}\n"
            f"{tati_row}\n\n"
            f"![image-{eid}]({png_file.split('/')[-1]})"
        )
        eid = build_id(d["tilo"])
        yield eid, markdown


def create_report_pdf(markdown_dir, data_path):
    for file in os.listdir(markdown_dir):
        os.system(f"grip {markdown_dir}/{file} --export {data_path}/html.html")
        os.system(
            f"wkhtmltopdf --enable-local-file-access -L 20 -R 20 {data_path}/html.html {data_path}/{file.replace('.md', '.pdf')}"
        )
    pdfs = [f"{data_path}/{f}" for f in os.listdir(data_path) if f.endswith(".pdf")]
    os.system(f"pdfunite {' '.join(pdfs)} radicacion_report.pdf")


if __name__ == "__main__":

    data_path = (
        f"{os.environ['HOME']}/data/corteconstitucional/procesos_tables/screenshots"
    )

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
    print(f"radicacion-differences: {len(diff_radicacion)}")
    markdown_dir = f"{data_path}/markdowns"
    os.makedirs(markdown_dir, exist_ok=True)

    for eid, md in generate_markdown_sections(diff_radicacion):
        data_io.write_file(f"{markdown_dir}/{eid}.md", md)

    create_report_pdf(markdown_dir, data_path)
