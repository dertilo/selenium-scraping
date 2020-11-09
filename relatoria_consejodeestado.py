import itertools
import os
import shutil
from datetime import timedelta, date
from typing import Tuple

import pandas
from selenium.webdriver.chrome.webdriver import WebDriver
from tqdm import tqdm
from util import data_io
from selenium import webdriver
from bs4 import BeautifulSoup


def build_chrome_driver(dir:str):
    os.makedirs(dir, exist_ok=True)
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    prefs = {"download.default_directory": dir}
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(
        r"/usr/bin/chromedriver", chrome_options=options
    )  # provide the chromedriver execution path in case of error
    driver.implicitly_wait(10)  # seconds
    return driver


def get_hits(page: str):
    soup = BeautifulSoup(page, features="html.parser")
    search_results = soup.find_all(class_="search-result")

    def get_link(sr):
        link = sr.find_all("a", href=True)
        if len(link) == 1:
            return {"path": str(link[0].attrs["href"]), "text": sr.text}
        else:
            return None

    g = (get_link(sr) for sr in search_results)
    g = (d for d in g if d is not None)
    return g


def build_doc(wd,hit):
    wd.get(f"{base_url}/{hit['path']}")
    soup = BeautifulSoup(wd.page_source, features="html.parser")
    if (
        "Lo sentimos mucho pero ese archivo todavía no está disponible para la página"
        in soup.text
    ):
        element = wd.find_element_by_xpath("/html/body/do/div/div/div/p[2]/a")
        element.click()
        # path = soup.find_all("p")[-1].find_all("a")[0].attrs["href"]
        # url = f"{base_url}/Document/{path}"
        doc = {"redirect": soup.text}
    else:
        doc = {"page": soup.text}
    doc.update(hit)
    return doc

def fmt(x):
    return str(x) if len(str(x))==2 else f"0{str(x)}"


def scrape_date_range(date_from:date,date_to:date,wd,data_path):
    year_from = date_from.year
    month_from = date_from.month
    day_from = date_from.day

    year_to = date_to.year
    month_to = date_to.month
    day_to = date_to.day

    date_range = f"{year_from}-{month_from}-{date_from}_{year_to}-{month_to}-{day_to}"
    for page in itertools.count(start=0):
        bucket_path = f"{data_path}/{date_range}_{page}"
        url = f"{base_url}/?de=0&se=0&ac=0&ca=0&rs={year_from}%2F{fmt(month_from)}%2F{fmt(day_from)}&re={year_to}%2F{fmt(month_to)}%2F{fmt(day_to)}&st=0&pg={page}"
        bucket_downloads = f"{bucket_path}/downloads"
        os.makedirs(bucket_downloads, exist_ok=True)

        docs_file = f"{bucket_path}/docs.jsonl"
        if os.path.isfile(docs_file):
            continue

        wd.get(url)
        source = wd.page_source
        if "No hay resultados para mostrar en este momento" in source:
            break

        docs = []
        for hit in get_hits(source):
            docs.append(build_doc(wd, hit))
            yield True

        data_io.write_jsonl(docs_file,docs)

        for file_name in os.listdir(download_path):
            shutil.move(os.path.join(download_path, file_name), bucket_downloads)


if __name__ == "__main__":

    base_url = "http://relatoria.consejodeestado.gov.co"
    data_path = f"{os.environ['HOME']}/data/relatoria_consejodeestado"
    download_path = f"{data_path}/downloads"
    wd = build_chrome_driver(download_path)


    dates = list(reversed(pandas.date_range("2010", "2020", freq="1M")+timedelta(days=1)))
    jobs = [
        (d1.date(), (d2 - timedelta(days=1)).date())
        for d1, d2 in zip(dates[:-1], dates[1:])
    ]
    os.listdir(data_path)
    g = (_ for s,e in jobs for _ in scrape_date_range(s,e,wd,data_path))

    for _ in tqdm(g):
        pass


