from __future__ import annotations

import argparse
import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.request import urlopen

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
INVOICE_ROOT = ROOT / "data" / "invoices"
SOURCE_ROOT = INVOICE_ROOT / "source"
CORPUS_PATH = SOURCE_ROOT / "waypoint-supplier-invoices.json"
TEMPLATE_ROOT = INVOICE_ROOT / "templates"
HTML_ROOT = INVOICE_ROOT / "html"
PDF_ROOT = INVOICE_ROOT / "pdf"
CORPUS_URL = (
    "https://raw.githubusercontent.com/caldova/waypoint/"
    "045637b6eea72550ce3aad61bfac851356ca824a/"
    "modules/corpus/data/invoices/supplier-invoices.json"
)
PALETTES = [
    ("#143f63", "#34a0a4", "#f2f7f8"),
    ("#493548", "#b86f52", "#f8f3f1"),
    ("#075968", "#20a4b8", "#eef8f9"),
    ("#24533d", "#79a85b", "#f1f7ef"),
    ("#5d4518", "#c69a38", "#faf6e9"),
    ("#334c70", "#7196c2", "#f1f5fa"),
    ("#6b3d35", "#cf826d", "#faf2ef"),
    ("#23566b", "#57a4bd", "#eef7fa"),
    ("#673b52", "#bd7897", "#faf1f5"),
    ("#303b47", "#778896", "#f2f4f5"),
    ("#314f59", "#6c9ba3", "#f1f6f7"),
    ("#4b4266", "#8d7cb3", "#f5f3f9"),
    ("#31583c", "#77a56e", "#f1f7f1"),
    ("#70471f", "#c48a42", "#faf4eb"),
    ("#3f4772", "#7783be", "#f2f3fa"),
]


def money(value: int | float) -> str:
    return f"${Decimal(str(value)):,.2f}"


def unit_price(value: int | float) -> str:
    number = Decimal(str(value))
    precision = 4 if number < 1 else 2
    return f"${number:,.{precision}f}"


def quantity(value: int | float) -> str:
    number = Decimal(str(value))
    return f"{number:,.0f}" if number == number.to_integral() else f"{number:,}"


def load_corpus(refresh: bool = False) -> dict[str, Any]:
    if refresh or not CORPUS_PATH.exists():
        SOURCE_ROOT.mkdir(parents=True, exist_ok=True)
        with urlopen(CORPUS_URL) as response:
            CORPUS_PATH.write_bytes(response.read())
    with CORPUS_PATH.open(encoding="utf-8") as source_file:
        return json.load(source_file)


def normalize_invoice(
    invoice: dict[str, Any], corpus: dict[str, Any]
) -> dict[str, Any]:
    profiles = {
        profile["supplier_id"]: profile
        for profile in corpus["document_generation"]["profiles"]
    }
    profile = profiles[invoice["supplier_id"]]
    billing = profile["billing_profile"]
    metadata = invoice["document_metadata"]
    supplier_number = int(invoice["supplier_id"].rsplit("-", 1)[-1])
    primary, accent, tint = PALETTES[supplier_number - 1]
    invoice_date = date.fromisoformat(invoice["invoice_date"])
    due_date = date.fromisoformat(metadata["due_date"])
    words = invoice["supplier_name"].split()

    normalized = {
        **invoice,
        "currency": corpus["currency"],
        "customer_account": billing["customer_account"],
        "due_date": metadata["due_date"],
        "payment_terms": f"Net {(due_date - invoice_date).days}",
        "profile_name": profile["profile_id"].replace("-", " ").title(),
        "remittance_reference": billing["remittance_reference"],
        "service_period": metadata["service_period"],
        "supplier_address": billing["address_lines"],
        "supplier_email": billing["billing_email"],
        "supplier_initials": "".join(word[0] for word in words[:2]).upper(),
        "support_references": metadata["support_references"],
        "tax_display": metadata["tax_display"],
        "theme": {"primary": primary, "accent": accent, "tint": tint},
    }
    normalized["lines"] = [
        {**line, "display_line_id": line["line_id"].rsplit("-", 1)[-1]}
        for line in invoice["lines"]
    ]
    return normalized


def validate_invoice(invoice: dict[str, Any]) -> None:

    calculated_total = sum(Decimal(str(line["amount"])) for line in invoice["lines"])
    declared_total = Decimal(str(invoice["total_amount"]))
    if calculated_total != declared_total:
        raise ValueError(
            f"Invoice lines total {calculated_total}, not declared total {declared_total}."
        )
    expected_prefix = f"{invoice['invoice_id']}-"
    if any(not line["line_id"].startswith(expected_prefix) for line in invoice["lines"]):
        raise ValueError(f"Invoice {invoice['invoice_id']} contains an invalid line ID.")


def render_html(invoice: dict[str, Any]) -> Path:
    environment = Environment(
        loader=FileSystemLoader(TEMPLATE_ROOT),
        autoescape=select_autoescape(("html", "xml")),
        undefined=StrictUndefined,
    )
    environment.filters["money"] = money
    environment.filters["unit_price"] = unit_price
    environment.filters["quantity"] = quantity
    template = environment.get_template(f"{invoice['supplier_id']}.html.j2")

    HTML_ROOT.mkdir(parents=True, exist_ok=True)
    html_path = HTML_ROOT / f"{invoice['invoice_id']}.html"
    html_path.write_text(
        template.render(
            invoice=invoice,
            logo_uri=(ROOT / "caldova_logo.png").as_uri(),
            supplier_logo_uri=(INVOICE_ROOT / "logos" / f"{invoice['supplier_id']}.svg").as_uri(),
        ),
        encoding="utf-8",
    )
    return html_path


def render_pdf(page: Any, html_path: Path) -> Path:
    PDF_ROOT.mkdir(parents=True, exist_ok=True)
    pdf_path = PDF_ROOT / f"{html_path.stem}.pdf"
    page.goto(html_path.as_uri(), wait_until="networkidle")
    page.pdf(path=pdf_path, format="Letter", print_background=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
    return pdf_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate supplier invoice HTML previews and PDFs.")
    parser.add_argument("invoice_id", nargs="?", default="INV-SUP-001-2026-10")
    parser.add_argument("--all", action="store_true", help="Generate every invoice in the corpus.")
    parser.add_argument("--refresh-source", action="store_true", help="Refresh the pinned Waypoint source.")
    args = parser.parse_args()

    corpus = load_corpus(args.refresh_source)
    source_invoices = corpus["invoices"]
    if not args.all:
        source_invoices = [
            invoice for invoice in source_invoices if invoice["invoice_id"] == args.invoice_id
        ]
        if not source_invoices:
            raise ValueError(f"Unknown invoice ID: {args.invoice_id}")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 816, "height": 1056})
        for source_invoice in source_invoices:
            invoice = normalize_invoice(source_invoice, corpus)
            validate_invoice(invoice)
            html_path = render_html(invoice)
            pdf_path = render_pdf(page, html_path)
            print(f"Generated {html_path.relative_to(ROOT)}")
            print(f"Generated {pdf_path.relative_to(ROOT)}")
        browser.close()


if __name__ == "__main__":
    main()