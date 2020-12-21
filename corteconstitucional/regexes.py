import regex

num2name = {
    1: "uno",
    2: "dos",
    3: "tres",
    4: "cuatro",
    5: "cinco",
    6: "seis",
    7: "siete",
    8: "ocho",
    9: "nueve",
    10: "diez",
    11: "once",
    12: "doce",
    13: "trece",
    14: "catorce",
    15: "quince",
    16: "dieciséis",
    17: "diecisiete",
    18: "dieciocho",
    19: "diecinueve",
    20: "veinte",
    21: "veintiuno",
    22: "veintidós",
    23: "veintitrés",
    24: "veinticuatro",
    25: "veinticinco",
    26: "veintiséis",
    27: "veintisiete",
    28: "veintiocho",
    29: "veintinueve",
    30: "treinta",
    31: "treinta y uno",
}
# fmt: off
name2num = {v: k for k, v in num2name.items()}
abbreviations = ["D", "LAT", "RE", "OG", "PE", "CAC", "CRF", "ICC", "E", "OP", "CJU", "RPZ", "RDL"]
anything = r'(?:.|\s)'
no_brackets = r'[^\)\(]'
expediente_code = rf"(?:{'|'.join(abbreviations)}){no_brackets}{{0,4}}-?{no_brackets}{{0,4}}\d{{1,9}}"
expediente_pattern = regex.compile(rf"expediente{anything}{{1,10}}{expediente_code}")
expediente_code_pattern = regex.compile(expediente_code)
sentencia_code = rf"(?:{'|'.join(['C'])})\s?-?\s?\d{{1,4}}(?:/\d{1,4})?"
sentencia_pattern = regex.compile(rf"Sentencia{anything}{{1,10}}{sentencia_code}")
sentencia_code_pattern = regex.compile(sentencia_code)
meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
meses = meses + [m.capitalize() for m in meses] +[m.upper() for m in meses]

meses_pattern = regex.compile(rf"{'|'.join(meses)}")
# CIRCLE = '(?:º|°)' # WTF there are different cirles!
CIRCLE = '\D{0,3}' # if gave up!
number_in_brackets = fr'\(\d{{1,5}}{CIRCLE}?\)'
number_in_brackets_pattern = regex.compile(number_in_brackets)
date_regex = rf"{number_in_brackets}{anything}{{1,100}}(?:{'|'.join(meses)}){anything}{{1,100}}{number_in_brackets}"
date_numeric_pattern = regex.compile(date_regex)
date_nonnum_regex = rf"(?:{'|'.join(num2name.values())}){anything}{{1,100}}(?:{'|'.join(meses)}){anything}{{1,100}}{number_in_brackets}"
date_nonnum_pattern = regex.compile(date_nonnum_regex)
NO_regex = "(?:N°|No\.)"
edicto_no_pattern = regex.compile(rf"EDICTO{anything}{{1,10}}{NO_regex}{anything}{{1,10}}\d{{1,4}}")
num_pattern = regex.compile(r"\d{1,4}")
# fmt: on

date_texts = [
    "Que la Sala Plena de esta Corporación en sesión del veintisiete (27) de Agosto de dos mil catorce (2014) adoptó la Sentencia N° **",
    # "LA SECRETARÍA GENERAL DE LA CORTE CONSTITUCIONAL NOTIFICA:  Que la Sala Plena de esta Corporación en sesión del primero (1°) de julio de dos mil veinte (2020) adoptó la Sentencia N° ",
]
date_texts_nonnum = [
]
if __name__ == "__main__":
    for text in date_texts:
        assert "°" in text
        matches = regex.compile(rf"{number_in_brackets}{anything}{{1,100}}(?:{'|'.join(meses)}){anything}{{1,100}}{number_in_brackets}").findall(text)
        # matches = regex.compile(rf"(?:{'|'.join(meses)})").findall(text)
        # matches = date_numeric_pattern.findall(text)
        print(matches)

    # for text in date_texts_nonnum:
    #     print(text)
    #     matches = regex.compile(rf"(?:{'|'.join(num2name.values())}){anything}{{1,100}}(?:{'|'.join(meses)}){anything}{{1,100}}{number_in_brackets}").findall(text)
    #     # matches = date_nonnum_pattern.findall(text)
    #     print(matches)
