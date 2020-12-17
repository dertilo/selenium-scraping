import traceback

import regex
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


def generate_raw_docs(
    old_docs: List[Dict],
    not_yet_done_hrefs: List[str],
    wd,
    download_dir,
    redo_errors=False,
):
    """
    raw cause they can be pdfs containig one edicto
    or HTMLs containing multiple edictos
    """

    def filter_done_docs(d):
        return ("error" not in d) if redo_errors else True

    done_docs = {d["href"]: d for d in old_docs if filter_done_docs(d)}

    print(f"already got: {len(done_docs.keys())}")
    not_yet_done_hrefs = [h for h in not_yet_done_hrefs if h not in done_docs.keys()]
    for href, doc in tqdm(done_docs.items()):
        yield doc

    for href in tqdm(not_yet_done_hrefs):
        if not href.endswith(".pdf"):
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
            datum = {"href": href, "link": link}

            wd.get(link)
            # TODO(tilo): I don't know (yet) how to wait for the download to finish!
            sleep(2)  # how long to wait?

            original_pdf_name = href.split("/")[-1]
            pdf_file_name = original_pdf_name.replace(" ", "_")
            try:
                shutil.move(
                    f"{download_dir}/{original_pdf_name}",
                    f"{download_dir}/{pdf_file_name}",
                )
                datum["pdf"] = pdf_file_name

            except BaseException:
                datum["error"] = "pdf not found"
                print(f"could not find {href}")
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
    """
    needs to be run several times, some times it claims that it cannot find downloaded pdfs,
    :param data_dir:
    :return:
    """
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
        data_io.write_jsonl(
            new_file, generate_raw_docs(old_docs, hrefs, wd, download_dir)
        )
    except BaseException:
        traceback.print_exc()
        print("shit happened")
    finally:
        if found_existing_documents:
            shutil.move(new_file, old_file)


valid_id_pattern = re.compile(r"\w{1,5}-\d{1,10}")
# fmt: off
abbreviations = ["D", "LAT", "RE", "OG", "PE", "CAC", "CRF", "ICC", "E", "OP", "CJU", "RPZ", "RDL"]
# fmt: on

# expediente_pattern = regex.compile(r"(?<=expediente.{1,100})\p{L}{1,5}\s?-?\s?\d{1,9}") # too lose
expediente_pattern = regex.compile(
    rf"(?<=expediente.{{1,100}})(?:{'|'.join(abbreviations)})\s?-?\s?\d{{1,9}}"
)


def generate_ids_from_edictos(
        data_dir=f"{os.environ['HOME']}/data/corteconstitucional/edictos"
    ):

    for d in data_io.read_jsonl(f"{data_dir}/documents.jsonl"):
        if "pdf" in d:
            pdf_file = f"{data_dir}/downloads/{d['pdf']}".replace(" ", "\ ")
            yield from parse_pdf(pdf_file)

        elif "html" in d:
            html = d["html"]
            for eid in expediente_pattern.findall(html):
                eid = fix_id(eid)
                assert is_valid_id(eid)
                yield eid


def is_valid_id(s):
    return valid_id_pattern.match(s) is not None


missing_dash = re.compile(r"\w{1,5}\d{1,10}")

exceptions = ["EDICTO_PUBLICADO_EN_PROCESO_DISCIPLINARIO_001-2018.pdf"]


def fix_id(eid: str):
    eid = eid.replace(" ", "").replace("\n", "")
    if missing_dash.match(eid) is not None:
        letters = regex.compile(r"\p{L}{1,5}").findall(eid)[0]
        numbers = regex.compile(r"\d{1,9}").findall(eid)[0]
        eid = f"{letters}-{numbers}"
    return eid


def parse_pdf(pdf_file):
    bytes = textract.process(pdf_file)
    text = bytes.decode("utf-8").replace("\n", " ")
    matches = expediente_pattern.findall(text)
    if len(matches) == 0 and pdf_file.split("/")[-1] not in exceptions:
        assert False

    def get_id(match):
        eid = fix_id(match)
        return eid

    # html_lines = exec_command(f"pdftohtml -noframes -stdout '{pdf_file}'")["stdout"]
    # html = "\n".join([l.decode("utf-8") for l in html_lines])
    # soup = BeautifulSoup(html, features="html.parser")
    ids = [get_id(m) for m in matches]
    assert all([is_valid_id(eid) for eid in ids])
    return ids


if __name__ == "__main__":
    # download_edictos()
    ids = list(generate_ids_from_edictos())
    print(len(ids))
    print(len(set(ids)))
    assert all([is_valid_id(eid) for eid in ids])
    print(set(eid.split("-")[0] for eid in ids))
    # data_io.write_lines("/tmp/ids.txt", ids)

    """
    got 2151 ids
    """
