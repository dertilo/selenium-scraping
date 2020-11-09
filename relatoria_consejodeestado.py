import os
from datetime import timedelta, date
from typing import Tuple

import pandas
from util import data_io
from selenium import webdriver
from bs4 import BeautifulSoup


def build_chrome_driver(data_path):
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    prefs = {"download.default_directory": data_path}
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


def scrape_date_range(date_from:date,date_to:date):
    year_from = date_from.year
    month_from = date_from.month
    day_from = date_from.day

    year_to = date_to.year
    month_to = date_to.month
    day_to = date_to.day

    page = 0

    bucket_name = f"from_{year_from}_{month_from}_{date_from}-to_{year_to}_{month_to}_{day_to}-page_{page}"
    data_path = f"{os.environ['HOME']}/data/relatoria_consejodeestado/{bucket_name}"
    os.makedirs(data_path, exist_ok=True)
    url = f"{base_url}/?de=0&se=0&ac=0&ca=0&rs={year_from}%2F{fmt(month_from)}%2F{fmt(day_from)}&re={year_to}%2F{fmt(month_to)}%2F{fmt(day_to)}&st=0&pg={page}"
    wd = build_chrome_driver(data_path)
    wd.get(url)
    g = get_hits(wd.page_source)
    data_io.write_jsonl(f"{data_path}/docs.jsonl", (build_doc(wd, hit) for hit in g))


if __name__ == "__main__":

    base_url = "http://relatoria.consejodeestado.gov.co"


    dates = pandas.date_range("2010", "2020", freq="1M")+timedelta(days=1)
    jobs = [
        (d1.date(), (d2 - timedelta(days=1)).date())
        for d1, d2 in zip(dates[:-1], dates[1:])
    ]

    scrape_date_range(jobs[0])
