import itertools
import os
import shutil
from datetime import timedelta
from datetime import timedelta, date
from typing import NamedTuple, List

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


def process_hits(download_path, data_path):
    wd = build_chrome_driver(download_path, headless=False)

    hits_files = [file for file in os.listdir(data_path) if file.startswith("hits")]
    for file in hits_files:
        with open(file, "r") as f:
            s = f.read()
        soup = BeautifulSoup(s, features="html.parser")


if __name__ == "__main__":
    base_url = "https://www.corteconstitucional.gov.co"
    data_path = f"{os.environ['HOME']}/data/corteconstitucional"
    gather_hits(base_url, data_path)

    # gather_hits()
