import traceback

from time import sleep

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
    soup = BeautifulSoup(html, features="html.parser")
    h2 = soup.find_all("h2")
    if len(h2) == 0:
        return False
    else:
        return h2[0].text == "404 - File or directory not found."


def get_hrefs(url, wd):
    wd.get(url)
    soup = BeautifulSoup(wd.page_source, features="html.parser")
    hrefs = list(set([x.attrs["href"] for x in soup.find_all("a") if x.attrs["href"]]))
    return hrefs


def generate_raw_docs(old_docs: List[Dict], hrefs, wd, download_dir,redo_errors=False):
    """
    raw cause they can be pdfs containig one edicto
    or HTMLs containing multiple edictos
    """
    def filter_done_docs(d):
        return ("error" not in d) if redo_errors else True
    done_docs = {d["href"]: d for d in old_docs if filter_done_docs(d)}

    print(f"already got: {len(done_docs.keys())}")

    for href in tqdm(hrefs):
        if href in done_docs.keys():
            datum = done_docs[href]
        elif not href.endswith(".pdf"):
            assert not href.startswith("secretaria/edictos/")
            link = f"https://www.corteconstitucional.gov.co/secretaria/edictos/{href}"
            wd.get(link)
            sleep(0.5)
            is_valid, html = get_valid_html(link, wd)

            datum = {"href": href, "link": link}
            if is_valid:
                datum["html"] = html
            else:
                print("document not found!")
                datum["error"] = "document not found"
        else:
            link = f"https://www.corteconstitucional.gov.co/{href}"
            wd.get(link)
            # TODO(tilo): I don't know (yet) how to wait for the download to finish!
            sleep(1)

            original_pdf_name = href.split("/")[-1]
            pdf_file_name = original_pdf_name.replace(" ", "_")
            shutil.move(
                f"{download_dir}/{original_pdf_name}", f"{download_dir}/{pdf_file_name}"
            )

            datum = {"href": href, "pdf": pdf_file_name, "link": link}
        yield datum


def get_valid_html(link, wd):
    try:  # just to trigger implicit wait
        _ = wd.find_element_by_xpath('//*[@id="logo"]')
        found_logo = True
    except BaseException:  # this is actually expected behavior cause there are many hrefs that lead to invalid links!
        print(f"{link}: has no logo?!?")
        found_logo = False

    html = wd.page_source
    is_valid = (not is_404(html)) and found_logo
    return is_valid, html


def download_edictos(
    data_dir=f"{os.environ['HOME']}/data/corteconstitucional/edictos",
):
    url = "https://www.corteconstitucional.gov.co/secretaria/edictos/"
    download_dir = f"{data_dir}/downloads"
    os.makedirs(download_dir, exist_ok=True)

    wd = build_chrome_driver(download_dir, headless=True)
    hrefs = get_hrefs(url, wd)

    old_file = f"{data_dir}/documents.jsonl"
    found_existing_documents = os.path.isfile(old_file)
    if found_existing_documents:
        new_file = old_file.split(".jsonl")[0] + "_updated.jsonl"
        old_docs = list(data_io.read_jsonl(old_file))
    else:
        old_docs = []
        new_file = old_file
    try:
        data_io.write_jsonl(new_file, generate_raw_docs(old_docs, hrefs, wd, download_dir))
    except BaseException:
        traceback.print_exc()
        print("shit happened")
    finally:
        if found_existing_documents:
            shutil.move(new_file, old_file)
    """
    100%|██████████| 149/149 [01:00<00:00,  2.47it/s]
    148
    """


def parse_docs():
    download_path = f"{os.environ['HOME']}/data/corteconstitucional/edictos"
    re.compile(r"expediente ")
    for d in data_io.read_jsonl(f"{download_path}/documents.jsonl"):
        if "pdf" in d:
            pdf_file = f"{download_path}/{d['pdf']}".replace(" ", "\ ")
            eid = parse_pdf(pdf_file)
            yield eid

        elif "html" in d:
            html = d["html"]
            expediente_and_id = r"expediente\s{1,10}[<>\w]{1,8}\w{1,5}-\d{1,10}"
            for match in re.compile(expediente_and_id).findall(html):
                eid = re.compile(r"\w{1,5}-\d{1,10}").search(match).group()
                yield eid


def parse_pdf(pdf_file):
    text = textract.process(pdf_file)
    match = (
        re.compile(r"expediente\s{1,10}\w{1,5}-\d{1,10}")
        .search(text.decode("utf-8"))
        .group()
    )
    eid = re.sub(r"expediente\s{1,10}", "", match)
    # html_lines = exec_command(f"pdftohtml -noframes -stdout '{pdf_file}'")["stdout"]
    # html = "\n".join([l.decode("utf-8") for l in html_lines])
    # soup = BeautifulSoup(html, features="html.parser")
    return eid


def fix_pdf_file_names(
    download_path=f"{os.environ['HOME']}/data/corteconstitucional/edictos",
):
    fixed_path = f"{download_path}_fixed"
    os.makedirs(fixed_path, exist_ok=True)

    def fix_doc(doc: Dict):
        if "pdf" in doc:
            pdf_file_name = doc["pdf"].replace(" ", "_")
            shutil.copy(
                f"{download_path}/{doc['pdf']}", f"{fixed_path}/{pdf_file_name}"
            )
            doc["pdf"] = pdf_file_name
        return doc

    docs_file = f"{download_path}/documents.jsonl"
    docs = list(data_io.read_jsonl(docs_file))
    data_io.write_jsonl(f"{fixed_path}/documents.jsonl", (fix_doc(d) for d in docs))


if __name__ == "__main__":
    download_edictos()
    # fix_pdf_file_names()
    # data_io.write_lines("/tmp/ids.txt", parse_docs())
