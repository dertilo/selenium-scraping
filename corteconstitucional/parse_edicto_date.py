import regex
from corteconstitucional.regexes import (
    anything,
    num_regex,
    MESES,
    number_in_brackets,
    meses_pattern,
    num_pattern,
)

# fmt: on
edicto_date_regex = rf"SE FIJA EN LA SECRETARÍA{anything}{{1,10}}HOY: {num_regex}{anything}{{1,10}}{MESES}{anything}{{1,40}}{number_in_brackets}"
edicto_date_pattern = regex.compile(edicto_date_regex)
# fmt: on

edicto_texts = [
    " LA SECRETARÍA GENERAL DE LA CORTE CONSTITUCIONAL NOTIFICA: Que la Sala Plena de esta Corporación en sesión del nueve (9) de septiembre de dos mil veinte (2020) adoptó la Sentencia N° C-393/20 dentro del expediente RE-330, cuya parte resolutiva dispuso: <<Declarar EXEQUIBLE el Decreto Legislativo 803 del 4 de junio de 2020 “Por medio del cual se crea el Programa de Apoyo para el Pago de la Prima de Servicios - PAP para el Sector Agropecuario, en el marco de la Emergencia Sanitaria ocasionada por el Coronavirus COVID 19”, con excepción de las siguientes disposiciones: (i) El numeral 1º del parágrafo 5° del artículo 3° que se declara INEXEQUIBLE. (ii) La expresión “La configuración de estos supuestos no conlleva responsabilidad para quienes participen en la implementación de este programa” contenida en el artículo 5°, parágrafo 3°, inciso 1°, que se declara EXEQUIBLE EN EL ENTENDIDO de que la misma no constituye una cláusula de inmunidad o de irresponsabilidad para los servidores públicos, sino que alude a la necesidad de que la valoración del dolo o culpa grave, presupuesto de la eventual responsabilidad en los casos allí previstos, debe tener en cuenta las condiciones de apremio y urgencia en las que se enmarca la implementación del programa. >> SE FIJA EN LA SECRETARÍA HOY: 6 DE OCTUBRE DE DOS MIL VEINTE (2020) HORA. 8:00 a. m.  _______________________ MARTHA VICTORIA SÁCHICA MÉNDEZ Secretaria General SE DESFIJA HOY: 8 DE OCTUBRE DE DOS MIL VEINTE (2020) HORA. 5:00 p. m.  _________________________ MARTHA VICTORIA SÁCHICA MÉNDEZ Secretaria General  "
]
year_pattern = regex.compile(fr"\d{{4}}")


def parse_edicto_date(text):
    m = edicto_date_pattern.search(text)
    if m is not None:
        s = text[m.start() : m.end()]
        month_match = meses_pattern.search(s)
        day_match = num_pattern.search(s[: month_match.start()])
        year_match = year_pattern.search(s[month_match.end() :])
        mes_i = MESES.index(month_match.group())
        day = int(day_match.group())
        year = year_match.group()
        date_s = f"{mes_i:02d}/{day:02d}/{year}"
    else:
        date_s = None
    return date_s


if __name__ == "__main__":
    for text in edicto_texts:
        parse_edicto_date(text)
