import re


LINE_RE = re.compile(
    r"""
    ^\s*
    (?P<t>[-+]?\d*\.?\d+)\s*s:\s*
    (?P<ch>C\d+)\s*=\s*
    (?P<val>[-+]?\d*\.?\d+)\s*
    (?P<unit>pF|nF|uF|µF|mF|F)\s*
    (?:\(\s*ADC\s*=\s*(?P<adc>\d+)\s*\))?
    """,
    re.VERBOSE | re.IGNORECASE,
)

UNIT_TO_PF = {
    "pf": 1.0,
    "nf": 1e3,
    "uf": 1e6,
    "µf": 1e6,
    "mf": 1e9,
    "f": 1e12,
}


def parse_cap_line(line: str):
    m = LINE_RE.search(line.strip())
    if not m:
        return None

    t = float(m.group("t"))
    ch = m.group("ch").upper()
    val = float(m.group("val"))
    unit = (m.group("unit") or "").replace("µ", "u").lower()
    unit_pf = UNIT_TO_PF.get(unit, 1.0)

    adc = m.group("adc")
    adc_int = int(adc) if adc is not None else None

    pretty_unit = unit.upper().replace("UF", "uF")
    if pretty_unit == "PF":
        pretty_unit = "pF"
    elif pretty_unit == "NF":
        pretty_unit = "nF"
    elif pretty_unit == "MF":
        pretty_unit = "mF"

    return {
        "time_s": t,
        "channel": ch,
        "cap_pf": val * unit_pf,
        "cap_value": val,
        "cap_unit": pretty_unit,
        "adc": adc_int,
    }