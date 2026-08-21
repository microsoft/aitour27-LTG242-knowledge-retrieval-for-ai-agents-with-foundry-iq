"""Inspect the chunked text generated for a PDF in the Search index.

This is a debugging helper for the Content Understanding indexing pipeline.
Use it to understand whether large PDF tables are being split across pages or
chunks and to tune chunking/retrieval parameters.
"""

from __future__ import annotations

import argparse
import html
import os
import shutil
from pathlib import Path
from textwrap import shorten

from azure.identity import AzureDeveloperCliCredential
from azure.search.documents import SearchClient
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
PDF_ROOT = REPO_ROOT / "sample-data" / "pdfs"

load_dotenv(dotenv_path=REPO_ROOT / ".env", override=True)

INDEX_NAME = "session-documents"
SELECT_FIELDS = [
    "chunk_id",
    "title",
    "blob_path",
    "chunk",
    "page_number_from",
    "page_number_to",
    "parent_id",
    "image_path",
]


def build_client() -> SearchClient:
    """Create a SearchClient using the local Azure developer credentials."""
    endpoint = os.environ.get("AZURE_AI_SEARCH_SERVICE_ENDPOINT")
    if not endpoint:
        raise RuntimeError(
            "AZURE_AI_SEARCH_SERVICE_ENDPOINT is not set. "
            "Run 'azd env get-values' or set the environment variable first."
        )

    credential = AzureDeveloperCliCredential(
        tenant_id=os.environ.get("AZURE_TENANT_ID"),
        process_timeout=60,
    )
    return SearchClient(endpoint=endpoint, index_name=INDEX_NAME, credential=credential)


def filter_results(results: list[dict], document_name: str | None, blob_path: str | None) -> list[dict]:
    """Filter results by document name or blob path."""
    filtered: list[dict] = []

    for result in results:
        title = str(result.get("title", "")).lower()
        blob = str(result.get("blob_path", "")).lower()

        if document_name:
            document_lower = document_name.lower()
            if document_lower not in title and document_lower not in blob:
                continue

        if blob_path and blob_path.lower() not in blob:
            continue

        filtered.append(result)

    return filtered


def format_chunk(chunk: dict) -> str:
    """Return a compact single-line summary for a chunk."""
    title = chunk.get("title") or "unknown"
    blob_path = chunk.get("blob_path") or "unknown"
    snippet = " ".join((chunk.get("chunk") or "").split())
    snippet = shorten(snippet, width=220, placeholder="...")
    return (
        f"- {title}\n"
        f"  blob: {blob_path}\n"
        f"  {page_label(chunk)}\n"
        f"  chunk: {snippet}\n"
    )


def page_label(chunk: dict) -> str:
    """Return a human-readable page range for a chunk."""
    page_from = chunk.get("page_number_from")
    page_to = chunk.get("page_number_to")
    if page_from is None and page_to is None:
        return "pages n/a"
    if page_to is None or page_from == page_to:
        return f"page {page_from or page_to}"
    if page_from is None:
        return f"page {page_to}"
    return f"pages {page_from}–{page_to}"


def copy_source_pdf(results: list[dict], output_file: Path) -> str | None:
    """Copy the local source PDF beside the report so the iframe can load it."""
    pdf_names = sorted(
        {
            str(result.get("title") or "")
            for result in results
            if str(result.get("title") or "").lower().endswith(".pdf")
        }
    )
    if len(pdf_names) != 1:
        return None

    source_pdf = PDF_ROOT / Path(pdf_names[0]).name
    if not source_pdf.is_file():
        return None

    destination = output_file.parent / source_pdf.name
    if source_pdf.resolve() != destination.resolve():
        shutil.copy2(source_pdf, destination)
    return destination.name


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Chunk viewer: __TITLE__</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; margin: 0; height: 100vh; display: flex; flex-direction: column; }
    h1 { font-size: 0.95rem; margin: 0; padding: 0.75rem 1rem; border-bottom: 1px solid #ddd; }
    .layout { flex: 1; display: grid; grid-template-columns: 1fr 1fr; min-height: 0; }
    .pane { min-height: 0; overflow: auto; }
    .pane.pdf { border-right: 1px solid #ddd; }
    iframe { width: 100%; height: 100%; border: 0; }
    .chunks { padding: 1rem; }
    .chunk-card { border: 1px solid #ddd; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.75rem; cursor: pointer; }
    .chunk-card:hover { border-color: #0078d4; }
    .chunk-card.active { border-color: #0078d4; box-shadow: 0 0 0 2px rgba(0, 120, 212, 0.15); }
    .chunk-card header { display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.4rem; }
    .badge { background: #0078d4; color: #fff; border-radius: 999px; padding: 0.1rem 0.6rem; font-size: 0.78rem; }
    .pages { color: #555; font-size: 0.85rem; }
    .chunk-id { color: #777; font-size: 0.72rem; margin: 0 0 0.5rem; word-break: break-all; }
    .chunk-text { white-space: pre-wrap; background: #f7f7f7; padding: 0.6rem; border-radius: 6px; margin: 0; font-size: 0.78rem; max-height: 20rem; overflow: auto; }
    .missing { padding: 1rem; color: #a80000; }
  </style>
</head>
<body>
  <h1>__TITLE__ — __COUNT__ chunk(s); click a chunk to jump to its first page</h1>
  <div class="layout">
    <div class="pane pdf">__VIEWER__</div>
    <div class="pane chunks">__CARDS__</div>
  </div>
  <script>
    const frame = document.getElementById('pdf-frame');
    const source = frame ? frame.getAttribute('src').split('#')[0] : null;
    document.querySelectorAll('.chunk-card').forEach((card) => {
      card.addEventListener('click', () => {
        document.querySelectorAll('.chunk-card').forEach((other) => other.classList.remove('active'));
        card.classList.add('active');
        if (frame && source) {
          frame.setAttribute('src', source + '#page=' + card.dataset.page);
        }
      });
    });
  </script>
</body>
</html>
"""


def write_html_report(results: list[dict], output_path: str) -> None:
    """Write a side-by-side report with the PDF next to its sequenced chunks."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    pdf_name = copy_source_pdf(results, output_file)

    cards = []
    for position, result in enumerate(results, start=1):
        start_page = result.get("page_number_from") or result.get("page_number_to") or 1
        cards.append(
            "<article class=\"chunk-card\" data-page=\"{page}\">"
            "<header><span class=\"badge\">Chunk {position}</span>"
            "<span class=\"pages\">{pages}</span></header>"
            "<p class=\"chunk-id\">{chunk_id}</p>"
            "<pre class=\"chunk-text\">{chunk_text}</pre>"
            "</article>".format(
                page=html.escape(str(start_page)),
                position=position,
                pages=html.escape(page_label(result)),
                chunk_id=html.escape(str(result.get("chunk_id", ""))),
                chunk_text=html.escape(str(result.get("chunk") or "")),
            )
        )

    document_title = next(
        (str(result.get("title")) for result in results if result.get("title")), "document"
    )
    viewer = (
        f'<iframe id="pdf-frame" src="{html.escape(pdf_name)}#page=1" title="Source PDF"></iframe>'
        if pdf_name
        else '<p class="missing">Local PDF not found under sample-data/pdfs.</p>'
    )

    html_report = (
        HTML_TEMPLATE.replace("__TITLE__", html.escape(document_title))
        .replace("__COUNT__", str(len(results)))
        .replace("__VIEWER__", viewer)
        .replace("__CARDS__", "\n".join(cards))
    )

    output_file.write_text(html_report, encoding="utf-8")
    print(f"Wrote HTML chunk report to {output_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--document",
        help="A filename or substring to match against the document title or blob path.",
    )
    parser.add_argument(
        "--blob-path",
        help="Exact or partial blob path to match, such as 'kb1/COA-MD-1026-A.pdf'.",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="Maximum number of chunks to return.",
    )
    parser.add_argument(
        "--html",
        help="Optional output path for an HTML chunk report; examples: debug/chunks.html.",
    )
    args = parser.parse_args()

    if not args.document and not args.blob_path:
        raise SystemExit("Provide --document or --blob-path.")

    client = build_client()
    results = client.search(
        search_text="*",
        select=SELECT_FIELDS,
        top=args.max_results,
    )
    rows = [dict(item) for item in results]

    rows = filter_results(rows, args.document, args.blob_path)
    rows = sorted(
        rows,
        key=lambda item: (
            item.get("page_number_from") is None,
            item.get("page_number_from") or 0,
            item.get("page_number_to") or 0,
            str(item.get("chunk_id") or ""),
        ),
    )

    if not rows:
        print("No chunks matched the requested document.")
        return

    print(f"Found {len(rows)} matching chunk(s).\n")
    for index, row in enumerate(rows, start=1):
        print(f"Chunk {index}:")
        print(format_chunk(row))

    if args.html:
        write_html_report(rows, args.html)


if __name__ == "__main__":
    main()
