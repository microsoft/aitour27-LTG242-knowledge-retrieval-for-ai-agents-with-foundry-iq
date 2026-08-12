from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = ROOT / "data" / "operational-reports"
SOURCE_PATH = REPORT_ROOT / "source" / "supplier-evidence.json"
WAYPOINT_PATH = ROOT / "data" / "invoices" / "source" / "waypoint-supplier-invoices.json"
TEMPLATE_ROOT = REPORT_ROOT / "templates"
HTML_ROOT = REPORT_ROOT / "html"
PDF_ROOT = REPORT_ROOT / "pdf"


def money(value: float) -> str:
    return f"${value:,.2f}"


def number(value: float | int) -> str:
    return f"{value:,.0f}"


def load_packets() -> list[dict[str, Any]]:
    with SOURCE_PATH.open(encoding="utf-8") as source_file:
        return json.load(source_file)["packets"]


def validate_packets(packets: list[dict[str, Any]]) -> None:
    with WAYPOINT_PATH.open(encoding="utf-8") as source_file:
        waypoint = json.load(source_file)
    invoices = {invoice["invoice_id"]: invoice for invoice in waypoint["invoices"]}

    for packet in packets:
        invoice = invoices[packet["invoice_id"]]
        source_text = json.dumps(invoice)
        required = [packet["evidence_id"], packet["invoice_line_id"], *packet["related_ids"]]
        missing = [reference for reference in required if reference not in source_text]
        if missing:
            raise ValueError(f"References absent from {packet['invoice_id']}: {', '.join(missing)}")
        line = next(line for line in invoice["lines"] if line["line_id"] == packet["invoice_line_id"])
        if line["amount"] != packet["invoice_amount"]:
            raise ValueError(f"Invoice amount mismatch for {packet['invoice_line_id']}")

        if packet["kind"] == "yield":
            overall = packet["overall"]
            calculated = round(overall["released_kg"] / overall["charged_kg"] * 100, 1)
            if calculated != overall["yield_percent"]:
                raise ValueError("Meridian overall yield is inconsistent.")
            forecast = packet["forecast"]
            if forecast["variance_kg"] * forecast["rate_per_kg"] != forecast["claimed_adjustment"]:
                raise ValueError("Meridian true-up arithmetic is inconsistent.")
        elif packet["kind"] == "inspection":
            summary = packet["summary"]
            if sum(lot["accepted"] for lot in packet["lots"]) != summary["accepted"]:
                raise ValueError("Keystone accepted quantity is inconsistent.")
            if sum(defect["quantity"] for defect in packet["defects"]) != summary["scrapped"]:
                raise ValueError("Keystone defect quantity is inconsistent.")
            if round(summary["built"] * summary["allowance_percent"] / 100) != summary["allowed_scrap"]:
                raise ValueError("Keystone scrap allowance is inconsistent.")
        else:
            capacity = packet["capacity"]
            if sum(run["hours"] for run in packet["runs"]) != capacity["utilized_hours"]:
                raise ValueError("BluePeak run hours are inconsistent.")
            if capacity["utilized_hours"] - capacity["included_hours"] != capacity["excess_hours"]:
                raise ValueError("BluePeak excess hours are inconsistent.")
            if capacity["excess_hours"] * capacity["excess_rate"] != capacity["excess_amount"]:
                raise ValueError("BluePeak excess charge is inconsistent.")


def report_context(packet: dict[str, Any]) -> dict[str, Any]:
    context: dict[str, Any] = {
        "packet": packet,
        "supplier_logo_uri": (ROOT / "data" / "invoices" / "logos" / f"{packet['supplier_id']}.svg").as_uri(),
        "caldova_logo_uri": (ROOT / "caldova_logo.png").as_uri(),
    }
    if packet["kind"] == "yield":
        maximum = packet["overall"]["charged_kg"]
        context["figure_rows"] = [{**stage, "bar_width": stage["output_kg"] / maximum * 100} for stage in packet["stages"]]
    elif packet["kind"] == "inspection":
        maximum = max(defect["quantity"] for defect in packet["defects"])
        context["figure_rows"] = [{**defect, "bar_width": defect["quantity"] / maximum * 100} for defect in packet["defects"]]
    else:
        capacity = packet["capacity"]
        context["included_width"] = capacity["included_hours"] / capacity["reserved_hours"] * 100
        context["excess_width"] = capacity["excess_hours"] / capacity["reserved_hours"] * 100
    return context


def render_html(packets: list[dict[str, Any]]) -> list[Path]:
    environment = Environment(
        loader=FileSystemLoader(TEMPLATE_ROOT),
        autoescape=select_autoescape(("html", "xml")),
        undefined=StrictUndefined,
    )
    environment.filters["money"] = money
    environment.filters["number"] = number
    HTML_ROOT.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for packet in packets:
        context = report_context(packet)
        for template_name, document_id in (
            ("evidence.html.j2", packet["evidence_id"]),
            ("assessment.html.j2", packet["assessment_id"]),
        ):
            html_path = HTML_ROOT / f"{document_id}.html"
            html_path.write_text(environment.get_template(template_name).render(**context), encoding="utf-8")
            outputs.append(html_path)
    return outputs


def render_pdfs(html_paths: list[Path]) -> list[Path]:
    PDF_ROOT.mkdir(parents=True, exist_ok=True)
    pdf_paths: list[Path] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 816, "height": 1056})
        for html_path in html_paths:
            pdf_path = PDF_ROOT / f"{html_path.stem}.pdf"
            page.goto(html_path.as_uri(), wait_until="networkidle")
            page.pdf(path=pdf_path, format="Letter", print_background=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
            pdf_paths.append(pdf_path)
        browser.close()
    return pdf_paths


def main() -> None:
    packets = load_packets()
    validate_packets(packets)
    html_paths = render_html(packets)
    pdf_paths = render_pdfs(html_paths)
    for html_path, pdf_path in zip(html_paths, pdf_paths, strict=True):
        print(f"Generated {html_path.relative_to(ROOT)}")
        print(f"Generated {pdf_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
