import re

import os
import regex
import textract
from util import data_io


valid_id_pattern = re.compile(r"\w{1,5}-\d{1,10}")

# fmt: off
abbreviations = ["D", "LAT", "RE", "OG", "PE", "CAC", "CRF", "ICC", "E", "OP", "CJU", "RPZ", "RDL"]
# expediente_pattern = regex.compile(r"(?<=expediente.{1,100})\p{L}{1,5}\s?-?\s?\d{1,9}") # too lose
expediente_pattern = regex.compile(rf"(?<=expediente.{{1,100}})(?:{'|'.join(abbreviations)})\s?-?\s?\d{{1,9}}")
# fmt: on

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

if __name__ == '__main__':
    ids = list(generate_ids_from_edictos())
    print(len(ids))
    print(len(set(ids)))
    assert all([is_valid_id(eid) for eid in ids])
    print(set(eid.split("-")[0] for eid in ids))
    # data_io.write_lines("/tmp/ids.txt", ids)

    """
    got 2151 ids
    """
