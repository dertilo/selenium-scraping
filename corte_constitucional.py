import itertools
import os
import shutil
from datetime import timedelta
from datetime import timedelta, date
from typing import NamedTuple, List, Dict

import pandas
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm
from util import data_io
from selenium.webdriver.support import expected_conditions as EC
from common import build_chrome_driver


def enter_keyboard_input(wd, xpath: str, value: str):
    # wait = WebDriverWait(wd, 10)
    # wait.until(EC.presence_of_element_located((By.xpath(value), "content")))
    e = wd.find_element_by_xpath(xpath)
    e.send_keys(value)
    e.send_keys(Keys.ENTER)


class Hit(NamedTuple):
    url: str
    page: int
    from_date: str
    to_date: str
    html: str


close_button = '//*[@id="cboxClose"]'
first_row = "/html/body/div[1]/div/table/tbody/tr[2]/td[1]/a"
next_one = '//*[@id="cboxNext"]'


def scrape_date_range(
    date_from: date, date_to: date, wd: WebDriver, data_path, base_url
):

    url = f"{base_url}/secretaria/"
    wd.get(url)

    click_it(wd, '//*[@id="formularioBT"]/div[2]/div[1]/div[3]/div/div[1]/label')
    enter_keyboard_input(wd, '//*[@id="DatoBuscar"]', "T")
    enter_keyboard_input(wd, '//*[@id="Fechadesde"]', date_from.strftime("%m/%d/%Y"))
    enter_keyboard_input(wd, '//*[@id="Fechahasta"]', date_to.strftime("%m/%d/%Y"))
    click_it(wd, '//*[@id="Buscar"]')

    hits = []
    hits.append(
        Hit(
            url=wd.current_url,
            page=0,
            from_date=date_from.strftime("%m/%d/%Y"),
            to_date=date_to.strftime("%m/%d/%Y"),
            html=wd.page_source,
        )._asdict()
    )

    for idx in itertools.count(start=1):
        soup = BeautifulSoup(wd.page_source, features="html.parser")
        siguiente = soup.find_all("a", string="Siguiente »")
        if len(siguiente) == 0:
            break
        url = f"{base_url}/secretaria/consultat/{siguiente[0].attrs['href']}"
        page = int(url.split("pg=")[-1])
        print(f"idx:{idx}; real-page:{page}")
        wd.get(url)
        hits.append(
            Hit(
                url=wd.current_url,
                page=page,
                from_date=date_from.strftime("%m/%d/%Y"),
                to_date=date_to.strftime("%m/%d/%Y"),
                html=wd.page_source,
            )._asdict()
        )

    from_to = f"{date_from.strftime('%m-%d-%Y')}-to-{date_to.strftime('%m-%d-%Y')}"
    data_io.write_jsonl(f"{data_path}/hits_{from_to}.jsonl", hits)


def dump_html(data_path, date_from, date_to, wd, page=0):
    source = wd.page_source
    from_to = f"{date_from.strftime('%m-%d-%Y')}-to-{date_to.strftime('%m-%d-%Y')}"
    data_io.write_file(
        f"{data_path}/hits_{from_to}_page_{page}.txt",
        source,
    )


def click_it(wd, xpath):
    element = wd.find_element_by_xpath(xpath)
    element.click()


def gather_hits(
    base_url="https://www.corteconstitucional.gov.co",
    data_path=f"{os.environ['HOME']}/data/corteconstitucional",
):
    download_path = f"{data_path}/downloads"
    wd = build_chrome_driver(download_path, headless=False)

    dates = list(
        reversed(pandas.date_range("2010", "2021", freq="1M") + timedelta(days=1))
    )
    # dates[0]-=timedelta(days=1) # cause it does not accept 2021!
    jobs = [
        (d1.date(), (d2 - timedelta(days=1)).date())
        for d1, d2 in zip(dates[:-1], dates[1:])
    ]
    scrape_date_range(jobs[0][1], jobs[0][0], wd, data_path, base_url)


import pandas as pd


def read_table(html: str) -> List[Dict]:
    """
    may be useful later
    """
    x = pd.read_html(html)
    df = x[0]
    header = df.loc[0].to_list()
    df = df[1:]
    df.columns = header
    x = df.to_dict("records")
    return x


def process_hits(data_path):
    download_path = f"{data_path}/downloads"
    wd = build_chrome_driver(download_path, headless=False)

    hits_files = [
        file
        for file in os.listdir(data_path)
        if file.startswith("hits") and file.endswith(".jsonl")
    ]
    for file in hits_files:
        file_name = file.replace("hits_", "details_")
        data_io.write_jsonl(
            f"{data_path}/{file_name}", generate_details(data_path, file, wd)
        )


def generate_details(data_path, file, wd):
    hits = [Hit(**d) for d in data_io.read_jsonl(f"{data_path}/{file}")]
    for hit in hits:
        rows = read_table(hit.html)
        ids = [r["RadicaciónExpediente"].split(" ")[1] for r in rows]
        for eid in ids:
            url = f"https://www.corteconstitucional.gov.co/secretaria/actuacion.php?palabra={eid}&proceso=2&sentencia=--"
            wd.get(url)
            yield {"id": eid, "html": wd.page_source}


if __name__ == "__main__":
    base_url = "https://www.corteconstitucional.gov.co"
    data_path = f"{os.environ['HOME']}/data/corteconstitucional"
    process_hits(data_path)
    # gather_hits(base_url, data_path)
