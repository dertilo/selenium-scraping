import os

from bs4 import BeautifulSoup
from tqdm import tqdm

from common import build_chrome_driver


def download_edictos_pdfs(
    download_path=f"{os.environ['HOME']}/data/corteconstitucional/edictos",
):
    url = "https://www.corteconstitucional.gov.co/secretaria/edictos/"
    wd = build_chrome_driver(download_path, headless=True)
    wd.get(url)
    soup = BeautifulSoup(wd.page_source, features="html.parser")
    links = soup.find_all("a")
    pdfs = list(
        set([x.attrs["href"] for x in links if x.attrs["href"].endswith(".pdf")])
    )
    for pdf in tqdm(pdfs):
        wd.get(f"https://www.corteconstitucional.gov.co/{pdf}")
    os.system(f"ls {download_path} | wc -l")  # number of documents
    """
    100%|██████████| 149/149 [01:00<00:00,  2.47it/s]
    148
    """


if __name__ == "__main__":
    download_edictos_pdfs()
