import os
from selenium.webdriver.support.select import Select
from time import sleep
from typing import List

from bs4 import BeautifulSoup
from util import data_io

from common import build_chrome_driver, click_it, enter_keyboard_input

DESDE = (
    "/html/body/div[2]/div/div[2]/div/div[11]/div/form/div[2]/div[2]/div/div[1]/input"
)
HASTA = (
    "/html/body/div[2]/div/div[2]/div/div[11]/div/form/div[2]/div[2]/div/div[2]/input"
)
SEARCH_INPUT = "/html/body/div[2]/div/div[2]/div/div[11]/div/form/div[2]/div[2]/div/div[3]/input[2]"
FIRST_ROW_POPUP = "/html/body/table/tbody/tr/td[1]/a"
POPUP_REFRESH_BUTTON = "/html/body/font/h1/a[1]/img"
BUSCADOR_DE_PROCESOS = '//*[@id="nav-tabs-wrapper"]/li[13]'


def scrape_proceso_tables(search_ids: List[str]):
    base_url = "https://www.corteconstitucional.gov.co/secretaria/"
    data_path = f"{os.environ['HOME']}/data/corteconstitucional/procesos_tables"
    os.makedirs(data_path, exist_ok=True)
    download_path = f"{data_path}/downloads"
    wd = build_chrome_driver(download_path, headless=False)

    for search_id in search_ids:
        file = f"{data_path}/{search_id}.json"
        if not os.path.isfile(file):
            fire_search(base_url, search_id, wd)
            datum = dump_proceso_table(wd)
            data_io.write_json(file,datum)


def dump_proceso_table(wd):
    click_it(wd, FIRST_ROW_POPUP)
    wd.switch_to.frame(0)
    click_it(wd, POPUP_REFRESH_BUTTON)
    # wd.switch_to.frame(0)
    html = wd.page_source
    soup = BeautifulSoup(html, features="html.parser")
    title = soup.find_all("title")[0].text
    assert "Proceso" in title
    name = "-".join([s for s in title.split(" ") if len(s) > 0])
    wd.switch_to.parent_frame()
    return {"name": name, "html": html}


abbrev2name = {
    "D": "Demanda Ordinaria",
    "LAT": "Ley aprobatoria de tratado",
    "ICC": "Conflictos de Competencia",
    "PE": "Proyecto de ley estatutaria",
    "CAC": "Convocatoria a asamblea constituyente",
    "CRF": "Convocatoria a referendo",
    "RE": "Decretos legislativos",
    "E": "Excusas",
    "OP": "Objeciones de inconstitucionalidad",
    # "NONE":"Tratados internacionales"
    "OG": "Objeciones gubernamentales",
    "CJU": "Conflictos de Jurisdicciones ",
    "RPZ": "Leyes y Actos Legislativos para la Paz",
    "RDL": "Decretos Leyes para la Paz",
}

PROCESO_TYPE_SELECTOR = (
    "/html/body/div[2]/div/div[2]/div/div[11]/div/form/div[2]/div[1]/div/div[1]/select"
)

BUILD_PROCSO_OPTION = (
    lambda i: f"/html/body/div[2]/div/div[2]/div/div[11]/div/form/div[2]/div[1]/div/div[1]/select/option[{i}]"
)


def fire_search(base_url, search_id, wd):
    wd.get(base_url)
    click_it(wd, BUSCADOR_DE_PROCESOS)

    option2id = build_option2id(wd)
    abbrev, number = search_id.split("-")

    select_proceso_type(abbrev, option2id, wd)

    enter_keyboard_input(wd, DESDE, "01/01/2000")
    enter_keyboard_input(wd, HASTA, "01/01/2021")
    enter_keyboard_input(wd, SEARCH_INPUT, number, clear_it=True, press_enter=True)


def select_proceso_type(abbrev, option2id, wd):
    name = abbrev2name[abbrev]
    i = option2id[name]
    option_name = wd.find_element_by_xpath(BUILD_PROCSO_OPTION(i)).text
    assert name == option_name
    click_it(wd, PROCESO_TYPE_SELECTOR)
    click_it(wd, BUILD_PROCSO_OPTION(i))


def build_option2id(wd):

    e = wd.find_element_by_xpath(PROCESO_TYPE_SELECTOR)
    sleep(0.5)
    no_spaces = " ".join([s for s in e.text.split(" ") if s != ""])
    split_by_newline = no_spaces.split("\n ")
    option_names = [x.replace("\n", "") for x in split_by_newline if x != ""]
    option2id = {o: i + 1 for i, o in enumerate(option_names)}
    return option2id


if __name__ == "__main__":

    scrape_proceso_tables(data_io.read_lines("/tmp/ids.txt",limit=10))
