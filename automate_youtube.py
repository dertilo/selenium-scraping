import os
from time import sleep

from selenium import webdriver
import pandas as pd
from selenium.webdriver.chrome.options import Options

from common import enter_keyboard_input, click_it

co = Options()
# chrome_options.add_argument("--headless")
co.add_argument("--no-sandbox")
co.add_argument("--window-size=1200x800")
user_data_dir = os.environ["HOME"]+"/.config/google-chrome" # TODO: this only works with ubuntu/linux
co.add_argument(f"--user-data-dir={user_data_dir}")
co.add_experimental_option("useAutomationExtension", False)
co.add_experimental_option("excludeSwitches", ["enable-automation"])
executable = '/usr/bin/chromedriver'
wd = webdriver.Chrome(options=co,
                      executable_path=executable)
wd.implicitly_wait(10)  # seconds

wd.get("https://www.youtube.com")
search_form = '//*[@id="search-form"]'
click_it(wd, search_form)

search_full = '/html/body/ytd-app/div/div/ytd-masthead/div[3]/div[2]/ytd-searchbox/form/div/div[1]/input' # only got it working with full xpath
video_title = '//*[@id="video-title"]/yt-formatted-string'

time_to_play_video = 2

search_strings = ["wtf", "hi andres!", "cholombianos", "tatiana patita", "pinguin"]
for search_string in search_strings:
    enter_keyboard_input(wd, search_full, search_string,clear_it=True)
    click_it(wd,video_title)
    sleep(time_to_play_video)

wd.quit()