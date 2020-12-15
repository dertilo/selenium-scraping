import os

from selenium import webdriver
from selenium.webdriver.common.keys import Keys


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


def enter_keyboard_input(wd, xpath: str, value: str,clear_it=False):
    # wait = WebDriverWait(wd, 10)
    # wait.until(EC.presence_of_element_located((By.xpath(value), "content")))
    e = wd.find_element_by_xpath(xpath)
    if clear_it:
        e.clear()
    e.send_keys(value)
    e.send_keys(Keys.ENTER)


def click_it(wd, xpath):
    element = wd.find_element_by_xpath(xpath)
    element.click()