import os

from selenium import webdriver
from selenium.webdriver.common.keys import Keys


def build_chrome_driver(download_dir: str, headless=True,window_size=(1920,1080)):
    os.makedirs(download_dir, exist_ok=True)
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("headless")

    w,h = window_size
    options.add_argument(f"--window-size={w},{h}")
    # driver.execute_script("document.body.style.zoom='80 %'")
    prefs = {
        "download.default_directory": download_dir,
        "plugins.always_open_pdf_externally": True, # don't open pdfs in browser but instead download them
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(
        r"/usr/bin/chromedriver", chrome_options=options
    )  # provide the chromedriver execution path in case of error
    driver.implicitly_wait(10)  # seconds
    return driver


def enter_keyboard_input(wd, xpath: str, value: str, clear_it=False,press_enter=False):
    # wait = WebDriverWait(wd, 10)
    # wait.until(EC.presence_of_element_located((By.xpath(value), "content")))
    e = wd.find_element_by_xpath(xpath)
    if clear_it:
        e.clear()
    e.send_keys(value)
    if press_enter:
        e.send_keys(Keys.ENTER)


def click_it(wd, xpath):
    element = wd.find_element_by_xpath(xpath)
    element.click()
