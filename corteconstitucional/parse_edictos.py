from typing import NamedTuple, List

import re

import os
import regex
import textract
from tqdm import tqdm
from util import data_io


valid_id_pattern = re.compile(r"\w{1,5}-\d{1,10}")

# fmt: off
abbreviations = ["D", "LAT", "RE", "OG", "PE", "CAC", "CRF", "ICC", "E", "OP", "CJU", "RPZ", "RDL"]
# expediente_pattern = regex.compile(r"(?<=expediente.{1,100})\p{L}{1,5}\s?-?\s?\d{1,9}") # too lose
expediente_code = rf"(?:{'|'.join(abbreviations)})\s?-?\s?\d{{1,9}}"
expediente_pattern = regex.compile(rf"(?<=expediente.{{1,100}}){expediente_code}")
fecha_sentencia_expediente_pattern = regex.compile(rf"del veintisiete (27) de noviembre de dos mil diecinueve (2019) adoptó la Sentencia N° C-569/19 dentro del expediente D-13178")
# fmt: on

class Edicto(NamedTuple):
    expediente:str

def extract_data(string:str)->List[Edicto]:
    matches = expediente_pattern.findall(string)
    ids = [fix_id(m) for m in matches]
    assert all([is_valid_id(eid) for eid in ids])

    return [Edicto(i) for i in ids]

def generate_ids_from_edictos(
        data_dir=f"{os.environ['HOME']}/data/corteconstitucional/edictos"
    ):

    for d in data_io.read_jsonl(f"{data_dir}/documents.jsonl"):
        if "pdf" in d:
            pdf_file = f"{data_dir}/downloads/{d['pdf']}".replace(" ", "\ ")
            text = parse_pdf(pdf_file)

        elif "html" in d:
            text = d["html"]
        else:
            text = ""

        yield from extract_data(text)


def is_valid_id(s):
    return valid_id_pattern.match(s) is not None


missing_dash = re.compile(r"\w{1,5}\d{1,10}")
KNOWN_TO_HAVE_NO_EXPEDIENTE = ["EDICTO_PUBLICADO_EN_PROCESO_DISCIPLINARIO_001-2018.pdf"]


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
    # if len(matches) == 0 and pdf_file.split("/")[-1] not in KNOWN_TO_HAVE_NO_EXPEDIENTE:
    #     assert False

    # html_lines = exec_command(f"pdftohtml -noframes -stdout '{pdf_file}'")["stdout"]
    # html = "\n".join([l.decode("utf-8") for l in html_lines])
    # soup = BeautifulSoup(html, features="html.parser")
    return text

if __name__ == '__main__':
    data = list(tqdm(generate_ids_from_edictos()))
    print(len(data))
    print(len(set(data)))
    print(set(d.expediente.split("-")[0] for d in data))
    # data_io.write_lines("/tmp/ids.txt", ids)

    """
    got 2151 ids
    """
