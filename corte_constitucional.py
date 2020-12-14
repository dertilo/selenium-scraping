import itertools
import os
import shutil
from datetime import timedelta
from datetime import timedelta, date

import pandas
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
    print(value)
    e = wd.find_element_by_xpath(xpath)
    e.send_keys(value)
    e.send_keys(Keys.ENTER)


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


def click_it(wd, xpath):
    element = wd.find_element_by_xpath(xpath)
    element.click()


def main():
    base_url = "https://www.corteconstitucional.gov.co"
    data_path = f"{os.environ['HOME']}/data/corteconstitucional"
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
    print(jobs[0])
    scrape_date_range(jobs[0][1], jobs[0][0], wd, data_path, base_url)


if __name__ == "__main__":
    main()
