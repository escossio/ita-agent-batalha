"""Sanitização de publicação da fonte HTML; não implementa runtime do ITA."""

import argparse
import hashlib
from pathlib import Path
import re


def sanitize(source: bytes) -> bytes:
    expected = "a96d4fe3c9d2591dfb2945f171d7a18e329cfb233ddfdd6a4ccb7948624eab23"
    if hashlib.sha256(source).hexdigest() != expected:
        raise ValueError("Fonte diferente da revisão aprovada; revisar antes de publicar")
    text = source.decode("utf-8")
    text, initials = re.subn(r'(<div class="circle">)[^<]+(</div>)', r'\1DEMO\2', text)
    text, card = re.subn(r"Cartão final \d{4}", "Cartão DEMO final 0000", text)
    if (initials, card) != (1, 1):
        raise ValueError("Estrutura de identificação inesperada")
    marker = (
        '<div role="note" style="padding:12px;background:#fff5ed">'
        'DEMO — cópia sanitizada de referência. Identificadores substituídos; '
        'valores ilustrativos. Não é o runtime do projeto ITA.</div>'
    )
    text = text.replace("</head><body>", "</head><body>\n" + marker, 1)
    return text.encode("utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    output = sanitize(args.source.read_bytes())
    with args.destination.open("xb") as destination:
        destination.write(output)
