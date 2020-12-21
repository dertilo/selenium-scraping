import html2text
from dataclasses import dataclass, asdict

from typing import List, Generator

import re

import os
import regex
import textract
from tqdm import tqdm
from util import data_io

from corteconstitucional.regexes import num2name, expediente_pattern, \
    expediente_code_pattern, sentencia_pattern, sentencia_code_pattern, meses, \
    meses_pattern, number_in_brackets_pattern, date_numeric_pattern, \
    date_nonnum_pattern, edicto_no_pattern, num_pattern, CIRCLE

valid_expediente_pattern = re.compile(r"\w{1,5}-\d{1,10}")


def is_valid_expediente(s):
    return valid_expediente_pattern.match(s) is not None


@dataclass(frozen=True, eq=True)
class Edicto:
    sentencia: str
    date: str
    expedientes: List[str]
    source: str
    no: int

    def __hash__(self):
        return hash((self.sentencia, *self.expedientes))


def extract_expedientes(string: str):
    matches = [
        e
        for s in expediente_pattern.findall(string)
        for e in expediente_code_pattern.findall(s)
    ]
    ids = [fix_expediente(m) for m in matches]
    assert all([is_valid_expediente(eid) for eid in ids])
    return ids


DEBUG_NO_DATE = "/tmp/no_date.txt"
DEBUG_RAW_TEXT = "/tmp/raw.txt"
DEBUG_BEFORE_SENTENCIA = "/tmp/before_sentencia.txt"
DEBUG_BEFORE_SENTENCIA_NO_DATE = "/tmp/before_sentencia_no_date.txt"
for f in [
    DEBUG_RAW_TEXT,
    DEBUG_BEFORE_SENTENCIA,
    DEBUG_BEFORE_SENTENCIA_NO_DATE,
    DEBUG_NO_DATE,
]:
    if os.path.isfile(f):
        os.remove(f)


def extract_date(string: str):
    dates_numeric = date_numeric_pattern.findall(string)
    dates_nonnum = date_nonnum_pattern.findall(string)

    if len(dates_numeric) >= 1:
        date_string = dates_numeric[
            -1
        ]  # take very last which is closest to sentencia mention!
        # return date_string
        mes = meses_pattern.search(date_string).group()
        mes_i = meses.index(mes) + 1
        day, year = [
            int(regex.sub(CIRCLE,"",s[1:-1]))
            for s in number_in_brackets_pattern.findall(date_string)
        ]
        date_s = f"{mes_i:02d}/{day:02d}/{year}"
        return date_s
    elif len(dates_nonnum) >= 1:

        date_nonnum = dates_nonnum[-1]
        mes = meses_pattern.search(date_nonnum).group()
        mes_i = meses.index(mes) + 1

        day = None
        for k in range(31, 1, -1):
            if num2name[k] in date_nonnum:
                day = k
                break
        assert day is not None
        year = [
            int(s[1:-1].replace("º", ""))
            for s in number_in_brackets_pattern.findall(date_nonnum)
        ][0]
        date_s = f"{mes_i:02d}/{day:02d}/{year}"
        return date_s
    else:
        data_io.write_lines(DEBUG_NO_DATE, [string], "ab")
        return None


def get_sentencia_span(m):
    outer_start = m.start()
    im = sentencia_code_pattern.search(m.group())
    return outer_start + im.start(), outer_start + im.end(), im.group()


def extract_data(source: str, string: str) -> Generator[Edicto, None, None]:
    edicto_nos = list(edicto_no_pattern.finditer(string))

    for k, m in enumerate(edicto_nos):
        edicto_end = (
            edicto_nos[k + 1].start() if k + 1 < len(edicto_nos) else len(string)
        )
        edicto_start = m.end()
        edicto_text = string[edicto_start:edicto_end]
        edicto_num = num_pattern.search(m.group()).group()
        # if edicto_num == 179:

        edictos = extract_from_edicto(source, edicto_text, edicto_num)
        yield from edictos


def extract_from_edicto(source, string, edicto_num: int):
    spans = [get_sentencia_span(m) for m in sentencia_pattern.finditer(string)]
    edictos = []
    for k, (start, end, sentencia) in enumerate(spans):
        next_start, _, _ = (
            spans[k + 1] if k + 1 < len(spans) else (len(string), None, None)
        )
        _, previous_end, _ = spans[k - 1] if k > 0 else (None, 0, None)
        behind_sentencia = string[end:next_start]
        expedientes = extract_expedientes(behind_sentencia)
        if len(expedientes) > 0:
            before_sentencia = string[previous_end:start]
            data_io.write_lines(
                DEBUG_BEFORE_SENTENCIA, [before_sentencia.replace("\n", "€")], mode="ab"
            )
            date = extract_date(before_sentencia)
            if date is not None:
                edictos.append(Edicto(sentencia, date, expedientes, source, edicto_num))
    if len(edictos) != 1:
        print()
    return edictos


KNOWN_TO_HAVE_NO_EXPEDIENTE = [
    "/secretaria/edictos/EDICTO PUBLICADO EN PROCESO DISCIPLINARIO 001-2018.pdf"
]
HREF_TO_EXCLUDE = ["editosanteriores.php", "?mes=18/12/2009"]


def generate_edictos(
    data_dir=f"{os.environ['HOME']}/data/corteconstitucional/edictos", limit=None
) -> Generator[Edicto, None, None]:

    g = (
        d
        for d in data_io.read_jsonl(f"{data_dir}/documents.jsonl")
        if d["href"] not in HREF_TO_EXCLUDE
    )
    for k, d in enumerate(g):
        if d["href"] in KNOWN_TO_HAVE_NO_EXPEDIENTE:
            continue
        if "pdf" in d:
            pdf_file = f"{data_dir}/downloads/{d['pdf']}".replace(" ", "\ ")
            text = parse_pdf(pdf_file)
            yield from extract_data(d["href"], text)

        elif "html" in d:
            text = html2text.html2text(d["html"])
            yield from extract_data(d["href"], text)
        if limit is not None and k > limit:
            break


missing_dash = re.compile(r"\w{1,5}\d{1,10}")


def fix_expediente(eid: str):
    eid = eid.replace(" ", "").replace("\n", "").replace("*", "")
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
    print(f"unique: {len(set(data))}")
    # print(set(d.expedientes[0].split("-")[0] for d in data))
    data_io.write_jsonl("edictos.jsonl", (asdict(d) for d in data))
    # data_io.write_jsonl("/tmp/texts.txt", data)

    """
    absolute number not that interesting cause one edicto can have multiple expedientes
    2193it [00:48, 45.15it/s]
    unique: 2181
    """
