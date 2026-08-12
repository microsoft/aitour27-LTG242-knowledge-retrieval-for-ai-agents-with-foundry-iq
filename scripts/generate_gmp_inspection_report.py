from __future__ import annotations

import json
import shutil
from datetime import date, datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = ROOT / "data" / "gmp-inspection-report"
SOURCE_PATH = REPORT_ROOT / "source" / "GMP-INS-BPB-2027-01.json"
WAYPOINT_PATH = ROOT / "data" / "invoices" / "source" / "waypoint-supplier-invoices.json"
EVIDENCE_PATH = ROOT / "data" / "operational-reports" / "source" / "supplier-evidence.json"
TEMPLATE_ROOT = REPORT_ROOT / "templates"
HTML_PATH = REPORT_ROOT / "html" / "GMP-INS-BPB-2027-01.html"
PDF_PATH = REPORT_ROOT / "pdf" / "GMP-INS-BPB-2027-01.pdf"
SCAN_ROOT = REPORT_ROOT / ".scan-pages"


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def date_en(value: str) -> str:
    return parse_date(value).strftime("%d %B %Y")


def date_short(value: str) -> str:
    return parse_date(value).strftime("%d %b %Y")


def load_report() -> dict[str, Any]:
    with SOURCE_PATH.open(encoding="utf-8") as source_file:
        return json.load(source_file)


def validate_report(report: dict[str, Any]) -> None:
    document = report["document"]
    inspection = report["inspection"]
    references = report["references"]
    summary = report["classification_summary"]
    deficiencies = report["deficiencies"]

    if document["report_id"] != "GMP-INS-BPB-2027-01":
        raise ValueError("Unexpected GMP inspection report ID.")
    if parse_date(inspection["start"]) > parse_date(inspection["end"]):
        raise ValueError("Inspection dates are not chronological.")
    if parse_date(inspection["end"]) > parse_date(document["issued"]):
        raise ValueError("Report issue date precedes the inspection.")

    calculated = {
        "critical": sum(item["classification"] == "Critical" for item in deficiencies),
        "major": sum(item["classification"] == "Major" for item in deficiencies),
        "other": sum(item["classification"] == "Other" for item in deficiencies),
    }
    if any(summary[key] != value for key, value in calculated.items()):
        raise ValueError("Deficiency summary does not match deficiency records.")
    if not report["system_findings"] or not report["capa_plan"] or len(report["attachments"]) < 3:
        raise ValueError("Inspection systems, CAPA plan, and attachments are required.")

    with WAYPOINT_PATH.open(encoding="utf-8") as source_file:
        waypoint = json.load(source_file)
    invoice = next(item for item in waypoint["invoices"] if item["invoice_id"] == references["invoice"])
    invoice_text = json.dumps(invoice)
    waypoint_required = (
        references["invoice_line"], references["purchase_order"], references["batch"],
        references["deviation"], references["utilization_log"],
        references["capacity"],
    )
    missing = [value for value in waypoint_required if value not in invoice_text]
    if missing:
        raise ValueError(f"References absent from pinned Waypoint invoice: {', '.join(missing)}")

    with EVIDENCE_PATH.open(encoding="utf-8") as source_file:
        packets = json.load(source_file)["packets"]
    packet = next(item for item in packets if item["invoice_id"] == references["invoice"])
    evidence_text = json.dumps(packet)
    evidence_required = (
        references["affected_run"], references["suite"], references["deviation"],
        report["event_summary"]["organism"], report["event_summary"]["root_cause"],
    )
    absent = [value for value in evidence_required if value not in evidence_text]
    if absent:
        raise ValueError(f"References absent from operational evidence: {', '.join(absent)}")


def render_html(report: dict[str, Any]) -> None:
    environment = Environment(
        loader=FileSystemLoader(TEMPLATE_ROOT),
        autoescape=select_autoescape(("html", "xml")),
        undefined=StrictUndefined,
    )
    environment.filters["date_en"] = date_en
    environment.filters["date_short"] = date_short
    context = {
        **report,
        "caldova_logo_uri": (ROOT / "caldova_logo.png").as_uri(),
        "connection_photo_uri": (REPORT_ROOT / "assets" / "tc4-transfer-connection.png").as_uri(),
        "pressure_photo_uri": (REPORT_ROOT / "assets" / "pressure-hold-station-v2.png").as_uri(),
    }
    HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
    HTML_PATH.write_text(
        environment.get_template("report.html.j2").render(**context),
        encoding="utf-8",
    )


def render_scanned_pdf() -> None:
    PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SCAN_ROOT.exists():
        shutil.rmtree(SCAN_ROOT)
    SCAN_ROOT.mkdir(parents=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 816, "height": 1056}, device_scale_factor=1.35)
        page.goto(HTML_PATH.as_uri(), wait_until="networkidle")
        page_elements = page.locator(".page")
        if page_elements.count() != 10:
            raise ValueError(f"Expected 10 report pages, found {page_elements.count()}.")

        scan_paths: list[Path] = []
        for index in range(page_elements.count()):
            scan_path = SCAN_ROOT / f"page-{index + 1:02d}.jpg"
            page_elements.nth(index).screenshot(path=scan_path, type="jpeg", quality=82)
            scan_paths.append(scan_path)

        scan_html = SCAN_ROOT / "scan.html"
        images = "".join(
            f'<section><img src="{path.as_uri()}" alt="Scanned report page {index}"></section>'
            for index, path in enumerate(scan_paths, start=1)
        )
        scan_html.write_text(
            "<!doctype html><style>@page{size:Letter;margin:0}*{box-sizing:border-box}"
            "html,body{margin:0}section{width:8.5in;height:11in;break-after:page;page-break-after:always}"
            "section:last-child{break-after:auto;page-break-after:auto}img{width:100%;height:100%;display:block}</style>"
            f"<body>{images}</body>",
            encoding="utf-8",
        )
        scan_page = browser.new_page(viewport={"width": 816, "height": 1056})
        scan_page.goto(scan_html.as_uri(), wait_until="networkidle")
        scan_page.pdf(
            path=PDF_PATH,
            format="Letter",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        browser.close()
    shutil.rmtree(SCAN_ROOT)


def main() -> None:
    report = load_report()
    validate_report(report)
    render_html(report)
    render_scanned_pdf()
    print(f"Generated clean HTML preview: {HTML_PATH.relative_to(ROOT)}")
    print(f"Generated scanned PDF:       {PDF_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()