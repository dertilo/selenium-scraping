import os
import re
import shutil
from pathlib import Path
from typing import List, Dict

import textract
from bs4 import BeautifulSoup
from tqdm import tqdm
from util import data_io
from util.util_methods import exec_command

from common import build_chrome_driver


def is_404(html):
    soup = BeautifulSoup(html)
    h2 = soup.find_all("h2")
    if len(h2)==0:
        return False
    else:
        return h2[0].text == '404 - File or directory not found.'


def download_edictos(
    download_path=f"{os.environ['HOME']}/data/corteconstitucional/edictos_1",
):
    url = "https://www.corteconstitucional.gov.co/secretaria/edictos/"
    wd = build_chrome_driver(download_path, headless=False)
    wd.get(url)
    soup = BeautifulSoup(wd.page_source, features="html.parser")
    hrefs = list(
        set([x.attrs["href"] for x in soup.find_all("a") if x.attrs["href"]])
    )

    def generate_raw_docs(old_docs:List[Dict]):
        """
        raw cause they can be pdfs containig one edicto
        or HTMLs containing multiple edictos
        """
        done_links = set([d["link"] for d in old_docs if not "error" in d])
        not_done_links = [l for l in hrefs if l not in done_links]
        print(f"already got: {len(done_links)}")

        for link in tqdm(not_done_links):
            if not link.endswith(".pdf"):
                assert not link.startswith("secretaria/edictos/")
                wd.get(f"https://www.corteconstitucional.gov.co/secretaria/edictos/{link}")
                html = wd.page_source

                datum = {"link":link}
                if not is_404(html):
                    datum["html"] = html
                else:
                    print("document not found!")
                    datum["error"] = "document not found"
            else:
                wd.get(f"https://www.corteconstitucional.gov.co/{link}")
                datum = {"link": link, "pdf":link.split("/")[-1]}
            yield datum

    file = f"{download_path}/documents.jsonl"
    if os.path.isfile(file):
        new_file = file.split(".jsonl")[0] + "_updated.jsonl"
        old_docs = list(data_io.read_jsonl(file))
    else:
        old_docs = []
        new_file = file
    data_io.write_jsonl(new_file,generate_raw_docs(old_docs))
    if new_file != file:
        shutil.move(new_file,file)
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
