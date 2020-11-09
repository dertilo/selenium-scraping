import os

from util import data_io
from selenium import webdriver
from bs4 import BeautifulSoup


def build_chrome_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    prefs = {"download.default_directory": download_path}
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


if __name__ == "__main__":

    base_url = "http://relatoria.consejodeestado.gov.co"
    year_from = 1900
    year_to = 2019
    month_to = 11
    day_to = 16
    page = 0

    folder_name = f"from_{year_from}-to_{year_to}_{month_to}_{day_to}-page_{page}"
    download_path = (
        f"{os.environ['HOME']}/data/relatoria_consejodeestado_downloads/{folder_name}"
    )
    os.makedirs(download_path, exist_ok=True)

    url = f"{base_url}/?de=0&se=0&ac=0&ca=0&rs={year_from}%2F01%2F01&re={year_to}%2F{month_to}%2F{day_to}&st=0&pg={page}"

    wd = (
        build_chrome_driver()
    )  # you can give three options here 1.Firefox 2.ChromeDriver 3.PhantomJS
    wd.get(url)

    g = get_hits(wd.page_source)

    def build_doc(hit):
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

    data_io.write_jsonl("docs.jsonl", (build_doc(hit) for hit in g))
