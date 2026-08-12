import json
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "procurement"
SOURCE_PATH = DATA_DIR / "source" / "procurement-chain.json"
TEMPLATE_DIR = DATA_DIR / "templates"
HTML_DIR = DATA_DIR / "html"
PDF_DIR = DATA_DIR / "pdf"


def load_source() -> dict[str, Any]:
    return json.loads(SOURCE_PATH.read_text())


def weighted_score(supplier: dict[str, Any], weights: list[dict[str, Any]]) -> float:
    score_keys = ["technical", "quality", "capacity", "commercial", "implementation"]
    return sum(
        supplier["scores"][key] * weights[index]["weight"] / 100
        for index, key in enumerate(score_keys)
    )


def validate_source(data: dict[str, Any]) -> None:
    suppliers = data["suppliers"]
    if len(suppliers) != 3:
        raise ValueError("Procurement package must contain exactly three suppliers")
    if sum(item["weight"] for item in data["rfp"]["weights"]) != 100:
        raise ValueError("RFP evaluation weights must total 100")
    if sum(1 for supplier in suppliers if supplier["selected"]) != 1:
        raise ValueError("Exactly one supplier must be selected")
    for supplier in suppliers:
        calculated = weighted_score(supplier, data["rfp"]["weights"])
        if abs(calculated - supplier["weighted_score"]) > 0.01:
            raise ValueError(f"Weighted score mismatch for {supplier['name']}")
        if supplier["annual_product_cost"] != round(
            supplier["unit_price"] * data["product"]["annual_volume"], 2
        ):
            raise ValueError(f"Annual product cost mismatch for {supplier['name']}")
        if supplier["year_one_total"] != supplier["annual_product_cost"] + supplier["tech_transfer_fee"]:
            raise ValueError(f"Year-one total mismatch for {supplier['name']}")
    po = data["purchase_order"]
    if sum(line["amount"] for line in po["lines"]) != po["subtotal"]:
        raise ValueError("Purchase-order lines do not sum to subtotal")
    if po["subtotal"] + po["tax"] != po["total"]:
        raise ValueError("Purchase-order total is inconsistent")
    selected = next(supplier for supplier in suppliers if supplier["selected"])
    if po["vendor_id"] != selected["vendor_id"] or po["supplier"] != selected["name"]:
        raise ValueError("Purchase order must name the selected supplier")
    if data["amendment"]["agreement_id"] != selected["agreement_id"]:
        raise ValueError("Amendment must modify the selected supplier agreement")
    chronology = [
        datetime.strptime(data["rfp"]["issue_date"], "%d %B %Y"),
        datetime.strptime(suppliers[0]["response_date"], "%d %B %Y"),
        datetime.strptime(data["rfp"]["award_notice"], "%d %B %Y"),
        datetime.strptime(data["amendment"]["effective_date"], "%d %B %Y"),
        datetime.strptime(po["issue_date"], "%d %B %Y"),
    ]
    if chronology != sorted(chronology):
        raise ValueError("RFP, response, award, amendment, and PO dates are not ordered")


def money(value: float) -> str:
    return f"${value:,.2f}"


def number(value: float) -> str:
    return f"{value:,.0f}"


def render_document(environment: Environment, template_name: str, output_id: str, **context: Any) -> Path:
    template = environment.get_template(template_name)
    output = HTML_DIR / f"{output_id}.html"
    output.write_text(template.render(**context))
    return output


def render_all_html(data: dict[str, Any]) -> list[tuple[str, Path]]:
    environment = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
        undefined=StrictUndefined,
    )
    environment.filters["money"] = money
    environment.filters["number"] = number
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    shared = {
        **data,
        "logo_uri": (ROOT / "caldova_logo.png").as_uri(),
        "suite_image_uri": (DATA_DIR / "assets" / "osd-manufacturing-suite.png").as_uri(),
    }
    outputs = [
        (data["rfp"]["document_id"], render_document(environment, "rfp.html.j2", data["rfp"]["document_id"], **shared))
    ]
    for supplier in data["suppliers"]:
        response_context = {**shared, "supplier": supplier}
        outputs.append((supplier["response_id"], render_document(environment, "response.html.j2", supplier["response_id"], **response_context)))
        outputs.append((supplier["agreement_id"], render_document(environment, "agreement.html.j2", supplier["agreement_id"], **response_context)))
    outputs.append((data["amendment"]["document_id"], render_document(environment, "amendment.html.j2", data["amendment"]["document_id"], **shared)))
    outputs.append((data["purchase_order"]["document_id"], render_document(environment, "purchase-order.html.j2", data["purchase_order"]["document_id"], **shared)))
    return outputs


def render_pdfs(outputs: list[tuple[str, Path]]) -> None:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1100, "height": 1424})
        for output_id, html_path in outputs:
            page.goto(html_path.as_uri(), wait_until="networkidle")
            page.pdf(
                path=PDF_DIR / f"{output_id}.pdf",
                format="Letter",
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                prefer_css_page_size=True,
            )
        browser.close()


def main() -> None:
    data = load_source()
    validate_source(data)
    outputs = render_all_html(data)
    render_pdfs(outputs)
    print(f"Generated {len(outputs)} HTML previews in {HTML_DIR.relative_to(ROOT)}")
    print(f"Generated {len(outputs)} searchable PDFs in {PDF_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
