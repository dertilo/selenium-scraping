from datetime import datetime

from pprint import pprint

from bs4 import BeautifulSoup
from tqdm import tqdm
from util import data_io

from common import build_chrome_driver


def generate(soup, year: int):
    for tr in soup.find_all("tr"):
        th = tr.find_all("th")
        td = tr.find_all("td")
        if len(th) > 0 and len(td) > 0:
            date = build_date(th, year)
            week_day, holiday_name, holiday_type = [t.text for t in td]
            yield {
                "date": date,
                "week_day": week_day,
                "holiday_name": holiday_name,
                "holiday_type": holiday_type,
            }


def build_date(th, year):
    day_s, month = th[0].text.split(" ")
    day = int(day_s)
    date_s = f"{month} {day} {year}"
    date = datetime.strptime(date_s, "%b %d %Y")
    date_formatted = date.strftime("%m/%d/%Y")
    return date_formatted


def get_holidays(wd, year):
    url = f"https://www.timeanddate.com/holidays/colombia/{year}?hol=1"
    wd.get(url)
    soup = BeautifulSoup(wd.page_source, features="html.parser")
    table = soup.find("section", class_="table-data__table")
    return list(generate(table, year))


if __name__ == "__main__":
    wd = build_chrome_driver("/tmp/", headless=True)
    first_year = 2015
    last_year = 2020
    data_io.write_jsonl(
        "holidays.jsonl",
        (d for year in tqdm(range(first_year, last_year + 1)) for d in get_holidays(wd, year)),
    )
    wd.close()
