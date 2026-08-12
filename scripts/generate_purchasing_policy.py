import json
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "purchasing-policy"
SOURCE_PATH = DATA_DIR / "source" / "caldova-purchasing-policy.json"
TEMPLATE_DIR = DATA_DIR / "templates"
HTML_PATH = DATA_DIR / "html" / "CAL-POL-PUR-001.html"
PDF_PATH = DATA_DIR / "pdf" / "CAL-POL-PUR-001.pdf"


def load_policy() -> dict[str, Any]:
    return json.loads(SOURCE_PATH.read_text())


def validate_policy(policy: dict[str, Any]) -> None:
    metadata = policy["metadata"]
    if metadata["document_id"] != "CAL-POL-PUR-001":
        raise ValueError("Unexpected purchasing policy document ID")

    approved = datetime.strptime(metadata["approved_on"], "%d %B %Y")
    effective = datetime.strptime(metadata["effective_from"], "%d %B %Y")
    review = datetime.strptime(metadata["next_review"], "%d %B %Y")
    if not approved <= effective < review:
        raise ValueError("Policy approval, effective, and review dates are not ordered")

    if len(policy["principles"]) != 6:
        raise ValueError("Purchasing policy must define exactly six principles")
    if len(policy["navigation"]) != 5:
        raise ValueError("Purchasing policy must define exactly five navigation sections")

    total_weight = sum(item["weight"] for item in policy["scorecard"])
    if total_weight != 100:
        raise ValueError(f"Supplier evaluation weights total {total_weight}, not 100")
    if not all(item["weight"] > 0 for item in policy["scorecard"]):
        raise ValueError("Supplier evaluation weights must be positive")
    if not any(item["gate"] for item in policy["scorecard"]):
        raise ValueError("Supplier evaluation must contain at least one mandatory gate")

    thresholds = policy["approval_thresholds"]
    minimums = [item["minimum"] for item in thresholds]
    if minimums != sorted(minimums) or len(minimums) != len(set(minimums)):
        raise ValueError("Approval thresholds must be unique and ascending")

    required_collections = [
        "roles",
        "sourcing_methods",
        "qualification_tiers",
        "qualification_rules",
        "lifecycle",
        "monitoring",
        "capa_steps",
        "ethics_rules",
        "responsible_supply",
        "buyer_commitments",
        "exception_fields",
    ]
    missing = [name for name in required_collections if not policy.get(name)]
    if missing:
        raise ValueError(f"Required policy sections are empty: {', '.join(missing)}")


def render_html(policy: dict[str, Any]) -> None:
    environment = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
        undefined=StrictUndefined,
    )
    template = environment.get_template("purchasing-policy.html.j2")
    HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
    HTML_PATH.write_text(template.render(**policy))


def render_pdf() -> None:
    PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1320, "height": 1020})
        page.goto(HTML_PATH.as_uri(), wait_until="networkidle")
        page.pdf(
            path=PDF_PATH,
            format="Letter",
            landscape=True,
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        browser.close()


def main() -> None:
    policy = load_policy()
    validate_policy(policy)
    render_html(policy)
    render_pdf()
    print(f"Rendered HTML: {HTML_PATH.relative_to(ROOT)}")
    print(f"Rendered PDF:  {PDF_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()