import os

from selenium import webdriver


def build_chrome_driver(download_dir:str,headless=True):
    os.makedirs(download_dir, exist_ok=True)
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("headless")
    prefs = {"download.default_directory": download_dir}
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(
        r"/usr/bin/chromedriver", chrome_options=options
    )  # provide the chromedriver execution path in case of error
    driver.implicitly_wait(10)  # seconds
    return driver