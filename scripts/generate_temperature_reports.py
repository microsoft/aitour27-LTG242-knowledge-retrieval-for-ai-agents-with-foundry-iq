from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = ROOT / "data" / "temperature-reports"
SOURCE_PATH = REPORT_ROOT / "source" / "valence-excursion.json"
WAYPOINT_PATH = ROOT / "data" / "invoices" / "source" / "waypoint-supplier-invoices.json"
TEMPLATE_ROOT = REPORT_ROOT / "templates"
HTML_ROOT = REPORT_ROOT / "html"
PDF_ROOT = REPORT_ROOT / "pdf"


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def display_time(value: str) -> str:
    return parse_time(value).strftime("%d %b %Y %H:%M UTC")


def duration(value: int) -> str:
    hours, minutes = divmod(value, 60)
    return f"{hours} hr {minutes} min" if minutes else f"{hours} hr"


def load_event() -> dict[str, Any]:
    with SOURCE_PATH.open(encoding="utf-8") as source_file:
        return json.load(source_file)


def validate_event(event: dict[str, Any]) -> None:
    readings = event["logger"]["readings"]
    reading_times = [parse_time(timestamp) for timestamp, _ in readings]
    values = [value for _, value in readings]
    excursion = event["excursion"]

    if reading_times != sorted(reading_times):
        raise ValueError("Logger readings must be in chronological order.")
    if readings[0][0] != event["logger"]["started_at"]:
        raise ValueError("First reading must match logger start time.")
    if readings[-1][0] != event["logger"]["stopped_at"]:
        raise ValueError("Last reading must match logger stop time.")
    if max(values) != excursion["maximum_temperature_c"]:
        raise ValueError("Logger peak does not match excursion summary.")

    calculated_duration = int(
        (parse_time(excursion["ended_at"]) - parse_time(excursion["started_at"])).total_seconds()
        / 60
    )
    if calculated_duration != excursion["duration_minutes"]:
        raise ValueError("Excursion timestamps do not match declared duration.")

    with WAYPOINT_PATH.open(encoding="utf-8") as source_file:
        waypoint = json.load(source_file)
    invoice = next(
        invoice
        for invoice in waypoint["invoices"]
        if invoice["invoice_id"] == event["references"]["invoice"]
    )
    source_text = json.dumps(invoice)
    required_references = (
        event["references"]["temperature_log"],
        event["references"]["investigation"],
        event["references"]["shipment"],
        event["references"]["proof_of_delivery"],
        event["references"]["lane_authorization"],
    )
    missing = [reference for reference in required_references if reference not in source_text]
    if missing:
        raise ValueError(f"References absent from pinned Waypoint invoice: {', '.join(missing)}")


def chart_context(event: dict[str, Any]) -> dict[str, Any]:
    readings = event["logger"]["readings"]
    start = parse_time(readings[0][0])
    end = parse_time(readings[-1][0])
    total_seconds = (end - start).total_seconds()
    plot = {"left": 58, "top": 18, "width": 672, "height": 226}
    y_min, y_max = 0.0, 12.0

    def x_position(timestamp: str) -> float:
        elapsed = (parse_time(timestamp) - start).total_seconds()
        return plot["left"] + (elapsed / total_seconds) * plot["width"]

    def y_position(value: float) -> float:
        return plot["top"] + ((y_max - value) / (y_max - y_min)) * plot["height"]

    points = [
        {"x": round(x_position(timestamp), 2), "y": round(y_position(value), 2), "value": value}
        for timestamp, value in readings
    ]
    path = " ".join(
        f"{'M' if index == 0 else 'L'} {point['x']} {point['y']}"
        for index, point in enumerate(points)
    )
    y_ticks = [
        {"value": value, "y": round(y_position(value), 2)}
        for value in (0, 2, 4, 6, 8, 10, 12)
    ]
    x_ticks = [
        {
            "label": parse_time(timestamp).strftime("%d %b\n%H:%M"),
            "x": round(x_position(timestamp), 2),
        }
        for timestamp, _ in readings[::6]
    ]
    if x_ticks[-1]["x"] != round(plot["left"] + plot["width"], 2):
        x_ticks.append(
            {
                "label": parse_time(readings[-1][0]).strftime("%d %b\n%H:%M"),
                "x": round(plot["left"] + plot["width"], 2),
            }
        )

    excursion_start = x_position(event["excursion"]["started_at"])
    excursion_end = x_position(event["excursion"]["ended_at"])
    return {
        "height": 286,
        "width": 760,
        "plot": plot,
        "path": path,
        "points": points,
        "x_ticks": x_ticks,
        "y_ticks": y_ticks,
        "low_y": round(y_position(event["logger"]["low_limit_c"]), 2),
        "high_y": round(y_position(event["logger"]["high_limit_c"]), 2),
        "excursion_x": round(excursion_start, 2),
        "excursion_width": round(excursion_end - excursion_start, 2),
    }


def report_context(event: dict[str, Any]) -> dict[str, Any]:
    values = [value for _, value in event["logger"]["readings"]]
    return {
        "event": event,
        "chart": chart_context(event),
        "summary": {
            "minimum": min(values),
            "maximum": max(values),
            "average": mean(values),
            "reading_count": len(values),
            "time_above": duration(event["excursion"]["duration_minutes"]),
        },
        "supplier_logo_uri": (ROOT / "data" / "invoices" / "logos" / "sup-008.svg").as_uri(),
        "caldova_logo_uri": (ROOT / "caldova_logo.png").as_uri(),
    }


def render_html(event: dict[str, Any]) -> list[Path]:
    environment = Environment(
        loader=FileSystemLoader(TEMPLATE_ROOT),
        autoescape=select_autoescape(("html", "xml")),
        undefined=StrictUndefined,
    )
    environment.filters["display_time"] = display_time
    environment.filters["duration"] = duration
    context = report_context(event)
    outputs = [
        ("logger-report.html.j2", event["references"]["temperature_log"]),
        ("investigation-report.html.j2", event["references"]["investigation"]),
    ]
    HTML_ROOT.mkdir(parents=True, exist_ok=True)
    html_paths = []
    for template_name, document_id in outputs:
        html_path = HTML_ROOT / f"{document_id}.html"
        html_path.write_text(
            environment.get_template(template_name).render(**context), encoding="utf-8"
        )
        html_paths.append(html_path)
    return html_paths


def render_pdfs(html_paths: list[Path]) -> list[Path]:
    PDF_ROOT.mkdir(parents=True, exist_ok=True)
    pdf_paths = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 816, "height": 1056})
        for html_path in html_paths:
            pdf_path = PDF_ROOT / f"{html_path.stem}.pdf"
            page.goto(html_path.as_uri(), wait_until="networkidle")
            page.pdf(
                path=pdf_path,
                format="Letter",
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
            pdf_paths.append(pdf_path)
        browser.close()
    return pdf_paths


def main() -> None:
    event = load_event()
    validate_event(event)
    html_paths = render_html(event)
    pdf_paths = render_pdfs(html_paths)
    for html_path, pdf_path in zip(html_paths, pdf_paths, strict=True):
        print(f"Generated {html_path.relative_to(ROOT)}")
        print(f"Generated {pdf_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
