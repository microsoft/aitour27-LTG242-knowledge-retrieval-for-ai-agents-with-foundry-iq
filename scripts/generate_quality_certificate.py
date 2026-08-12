from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
CERTIFICATE_ROOT = ROOT / "data" / "quality-certificate"
SOURCE_PATH = CERTIFICATE_ROOT / "source" / "COA-MD-1026-A.json"
WAYPOINT_PATH = ROOT / "data" / "invoices" / "source" / "waypoint-supplier-invoices.json"
TEMPLATE_ROOT = CERTIFICATE_ROOT / "templates"
HTML_PATH = CERTIFICATE_ROOT / "html" / "COA-MD-1026-A.html"
PDF_PATH = CERTIFICATE_ROOT / "pdf" / "COA-MD-1026-A.pdf"


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def date_es(value: str) -> str:
    months = (
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    )
    parsed = parse_date(value)
    return f"{parsed.day:02d} de {months[parsed.month - 1]} de {parsed.year}"


def number_es(value: int | float) -> str:
    return f"{value:,.0f}".replace(",", ".")


def load_certificate() -> dict[str, Any]:
    with SOURCE_PATH.open(encoding="utf-8") as source_file:
        return json.load(source_file)


def validate_certificate(certificate: dict[str, Any]) -> None:
    references = certificate["references"]
    document = certificate["document"]
    dates = certificate["dates"]
    tests = certificate["tests"]

    if document["certificate_id"] != "COA-MD-1026-A":
        raise ValueError("El identificador del certificado no es el esperado.")
    if document["language"] != "Español":
        raise ValueError("El certificado debe emitirse únicamente en español.")

    chronology = [
        dates["manufacturing_start"], dates["manufacturing_end"], dates["sampling"],
        dates["analysis_start"], dates["analysis_end"], dates["issued"], dates["retest"],
    ]
    parsed_dates = [parse_date(value) for value in chronology]
    if parsed_dates != sorted(parsed_dates):
        raise ValueError("Las fechas del certificado no están en orden cronológico.")

    sequences = [item["sequence"] for item in tests]
    if sequences != list(range(1, len(tests) + 1)):
        raise ValueError("La secuencia de ensayos debe ser continua.")
    if len(tests) < 10:
        raise ValueError("El certificado debe contener una tabla analítica sustantiva.")
    if any(not item.get("test") or not item.get("method") or not item.get("acceptance") or not item.get("result") for item in tests):
        raise ValueError("Todos los ensayos deben incluir método, criterio y resultado.")
    if any(item["status"] != "Conforme" for item in tests):
        raise ValueError("El estado liberado exige que todos los ensayos sean conformes.")
    if certificate["disposition"]["status"] != "LIBERADO":
        raise ValueError("La disposición debe coincidir con los resultados conformes.")

    with WAYPOINT_PATH.open(encoding="utf-8") as source_file:
        waypoint = json.load(source_file)
    invoice = next(
        item for item in waypoint["invoices"]
        if item["invoice_id"] == references["invoice"]
    )
    source_text = json.dumps(invoice)
    required = (
        document["certificate_id"], references["lot"], references["yield_worksheet"],
        references["manufacturing_record"], references["raw_material_packet"],
        certificate["material"]["name"], references["invoice_line"],
    )
    missing = [value for value in required if value not in source_text]
    if missing:
        raise ValueError(f"Referencias ausentes de la factura Waypoint: {', '.join(missing)}")

    invoice_line = next(line for line in invoice["lines"] if line["line_id"] == references["invoice_line"])
    if invoice_line["quantity"] != certificate["material"]["batch_size_kg"]:
        raise ValueError("La cantidad liberada no coincide con la línea de factura.")


def render_html(certificate: dict[str, Any]) -> None:
    environment = Environment(
        loader=FileSystemLoader(TEMPLATE_ROOT),
        autoescape=select_autoescape(("html", "xml")),
        undefined=StrictUndefined,
    )
    environment.filters["date_es"] = date_es
    environment.filters["number_es"] = number_es
    context = {
        **certificate,
        "supplier_logo_uri": (ROOT / "data" / "invoices" / "logos" / "sup-004.svg").as_uri(),
    }
    HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
    HTML_PATH.write_text(
        environment.get_template("certificate.html.j2").render(**context),
        encoding="utf-8",
    )


def render_pdf() -> None:
    PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 816, "height": 1056})
        page.goto(HTML_PATH.as_uri(), wait_until="networkidle")
        page.pdf(
            path=PDF_PATH,
            format="Letter",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        browser.close()


def main() -> None:
    certificate = load_certificate()
    validate_certificate(certificate)
    render_html(certificate)
    render_pdf()
    print(f"Generated {HTML_PATH.relative_to(ROOT)}")
    print(f"Generated {PDF_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()