import os
from time import sleep
from typing import List

from bs4 import BeautifulSoup
from util import data_io

from common import build_chrome_driver, click_it, enter_keyboard_input

DESDE = '/html/body/div[2]/div/div[2]/div/div[11]/div/form/div[2]/div[2]/div/div[1]/input'
HASTA = '/html/body/div[2]/div/div[2]/div/div[11]/div/form/div[2]/div[2]/div/div[2]/input'
SEARCH_INPUT = '/html/body/div[2]/div/div[2]/div/div[11]/div/form/div[2]/div[2]/div/div[3]/input[2]'
FIRST_ROW_POPUP = '/html/body/table/tbody/tr/td[1]/a'
POPUP_REFRESH_BUTTON = '/html/body/font/h1/a[1]/img'
BUSCADOR_DE_PROCESOS = '//*[@id="nav-tabs-wrapper"]/li[13]'


def scrape_proceso_tables(search_ids:List[str]):
    base_url = "https://www.corteconstitucional.gov.co/secretaria/"
    data_path = f"{os.environ['HOME']}/data/corteconstitucional/procesos_tables"
    os.makedirs(data_path, exist_ok=True)
    download_path = f"{data_path}/downloads"
    wd = build_chrome_driver(download_path, headless=False)
    for search_id in search_ids:
        dump_proceso_table(search_id, wd, base_url, data_path)


def dump_proceso_table(search_id, wd, base_url, data_path):
    wd.get(base_url)
    click_it(wd, BUSCADOR_DE_PROCESOS)
    enter_keyboard_input(wd, DESDE, "01/01/2000")
    enter_keyboard_input(wd, HASTA, "01/01/2021")
    enter_keyboard_input(wd, SEARCH_INPUT, search_id)
    click_it(wd, FIRST_ROW_POPUP)
    wd.switch_to.frame(0)
    click_it(wd, POPUP_REFRESH_BUTTON)
    wd.switch_to.frame(0)
    html = wd.page_source
    soup = BeautifulSoup(html, features="html.parser")
    title = soup.find_all("title")[0].text
    assert "Proceso" in title
    name = "-".join([s for s in title.split(" ") if len(s) > 0])
    data_io.write_json(f"{data_path}/{name}.json", {"name": name, "html": html})
    wd.switch_to.parent_frame()
    # click_it(wd, '/html/body/table/tbody/tr/td[6]/a')
    # click_it(wd,'//*[@id="cboxClose"]')


if __name__ == '__main__':

    scrape_proceso_tables()
