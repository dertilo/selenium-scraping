from dataclasses import dataclass, asdict

from typing import NamedTuple, List, Generator

import re

import os
import regex
import textract
from tqdm import tqdm
from util import data_io


valid_expediente_pattern = re.compile(r"\w{1,5}-\d{1,10}")

# fmt: off
abbreviations = ["D", "LAT", "RE", "OG", "PE", "CAC", "CRF", "ICC", "E", "OP", "CJU", "RPZ", "RDL"]
# expediente_pattern = regex.compile(r"(?<=expediente.{1,100})\p{L}{1,5}\s?-?\s?\d{1,9}") # too lose
btag = '(?:</?b>)'
expediente_code = rf"(?:{'|'.join(abbreviations)})\s?{btag}?-?{btag}?\s?\d{{1,9}}"
expediente_pattern = regex.compile(rf"(?<=expediente.{{1,100}}){expediente_code}")

sentencia_code = rf"(?:{'|'.join(['C'])})\s?-?\s?\d{{1,4}}(?:/\d{1,4})?"
sentencia_pattern = regex.compile(rf"(?<=Sentencia.{{1,100}}){sentencia_code}")
meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
# date_pattern = regex.compile(rf"\(\d{{1,2}}\).{1,30}(?:{'|'.join(meses)}).{1,30}\(\d{{4}}\)")
date_pattern = regex.compile(rf"(?:{'|'.join(meses)})")
# fmt: on


def is_valid_expediente(s):
    return valid_expediente_pattern.match(s) is not None


@dataclass(frozen=True, eq=True)
class Edicto:
    sentencia: str
    date: str
    expedientes: List[str]
    source: str

    def __hash__(self):
        return hash((self.sentencia, *self.expedientes))


def extract_expedientes(string: str):
    matches = expediente_pattern.findall(string)
    ids = [fix_expediente(m) for m in matches]
    assert all([is_valid_expediente(eid) for eid in ids])
    return ids


def extract_date(string: str):
    dates = date_pattern.findall(string)
    return dates[0] if len(dates) == 1 else None


DEBUG_RAW_TEXT = "/tmp/raw.txt"


def extract_data(source: str, string: str) -> Generator[Edicto, None, None]:
    matches = list(sentencia_pattern.finditer(string))
    spans = [(m.start(), m.end(), m.group()) for m in matches]
    for k, (start, end, sentencia) in enumerate(spans):
        next_start, *_ = spans[k + 1] if k + 1 < len(spans) else (len(string),)
        _, previous_end, _ = spans[k - 1] if k > 0 else (None, 0, None)
        behind_sentencia = string[end:next_start]
        expedientes = extract_expedientes(behind_sentencia)
        if len(expedientes) > 0:
            before_sentencia = string[previous_end:start]
            date = extract_date(before_sentencia)
            if date is not None:
                yield Edicto(sentencia, date, expedientes, source)


def generate_edictos(
    data_dir=f"{os.environ['HOME']}/data/corteconstitucional/edictos",
) -> Generator[Edicto, None, None]:

    for d in data_io.read_jsonl(f"{data_dir}/documents.jsonl"):
        if "pdf" in d:
            pdf_file = f"{data_dir}/downloads/{d['pdf']}".replace(" ", "\ ")
            text = parse_pdf(pdf_file)
            yield from extract_data(d["href"], text)

        elif "html" in d:
            text = d["html"]
            data_io.write_lines(DEBUG_RAW_TEXT, text.split("\n"), mode="ab")

            yield from extract_data(d["href"], text)


missing_dash = re.compile(r"\w{1,5}\d{1,10}")
KNOWN_TO_HAVE_NO_EXPEDIENTE = ["EDICTO_PUBLICADO_EN_PROCESO_DISCIPLINARIO_001-2018.pdf"]


def fix_expediente(eid: str):
    eid = eid.replace(" ", "").replace("\n", "")
    eid = regex.sub(rf"{btag}", "", eid)
    if missing_dash.match(eid) is not None:
        letters = regex.compile(r"\p{L}{1,5}").findall(eid)[0]
        numbers = regex.compile(r"\d{1,9}").findall(eid)[0]
        eid = f"{letters}-{numbers}"
    return eid


def parse_pdf(pdf_file) -> str:
    bytes = textract.process(pdf_file)
    text_with_linebreaks = bytes.decode("utf-8")
    data_io.write_lines(DEBUG_RAW_TEXT, text_with_linebreaks.split("\n"), mode="ab")

    text = text_with_linebreaks.replace("\n", " ")

    # if len(matches) == 0 and pdf_file.split("/")[-1] not in KNOWN_TO_HAVE_NO_EXPEDIENTE:
    #     assert False

    # html_lines = exec_command(f"pdftohtml -noframes -stdout '{pdf_file}'")["stdout"]
    # html = "\n".join([l.decode("utf-8") for l in html_lines])
    # soup = BeautifulSoup(html, features="html.parser")
    return text


if __name__ == "__main__":
    data = list(tqdm(generate_edictos()))
    print(len(data))
    print(len(set(data)))
    # print(set(d.expedientes[0].split("-")[0] for d in data))
    data_io.write_jsonl("/tmp/edictos.jsonl", (asdict(d) for d in data))
    # data_io.write_jsonl("/tmp/texts.txt", data)

    """
    got 2151 ids
    with "date"
    1767it [00:03, 455.90it/s]
    """
