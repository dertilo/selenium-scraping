import os
import re
from pathlib import Path

import textract
from bs4 import BeautifulSoup
from tqdm import tqdm
from util import data_io
from util.util_methods import exec_command

from common import build_chrome_driver


def download_edictos(
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

def parse_pdfs():
    download_path=f"{os.environ['HOME']}/data/corteconstitucional/edictos"
    re.compile(r"expediente ")
    for file in Path(download_path).rglob("*.pdf"):
        pdf_file = f"{download_path}/{file.name}"
        text = textract.process(pdf_file)
        match = re.compile(r"expediente\s{1,10}\w{1,5}-\d{1,10}").search(text.decode("utf-8")).group()
        eid = re.sub(r"expediente\s{1,10}","",match)
        # html_lines = exec_command(f"pdftohtml -noframes -stdout '{pdf_file}'")["stdout"]
        # html = "\n".join([l.decode("utf-8") for l in html_lines])
        # soup = BeautifulSoup(html, features="html.parser")
        yield eid



if __name__ == "__main__":
    download_edictos()
