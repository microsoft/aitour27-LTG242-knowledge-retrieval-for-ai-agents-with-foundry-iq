"""Synchronize the tracked runtime data from the Caldova sample-data repository."""

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).parents[1]
DEFAULT_SOURCE = REPO_ROOT.parent / "aitour27-caldova-data"
TARGET_ROOT = REPO_ROOT / "sample-data"
MANIFEST_PATH = Path("sample-data/corpora.json")
JSON_SOURCE_DIR = Path("sample-data/json")


def git_output(source: Path, *arguments: str) -> str:
    """Return one Git value from the upstream checkout."""
    result = subprocess.run(
        ["git", "-C", str(source), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def load_manifest(source: Path) -> tuple[dict[str, list[str]], list[Path]]:
    """Validate the corpus manifest and return all listed PDF paths."""
    manifest_file = source / MANIFEST_PATH
    try:
        manifest: Any = json.loads(manifest_file.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise RuntimeError(f"Missing upstream manifest: {manifest_file}") from error

    if not isinstance(manifest, dict) or not manifest:
        raise RuntimeError("The upstream corpus manifest must contain named groups.")

    normalized: dict[str, list[str]] = {}
    relative_paths: list[Path] = []
    for corpus_name, files in manifest.items():
        if not isinstance(corpus_name, str) or not corpus_name:
            raise RuntimeError("Every corpus must have a non-empty string name.")
        if not isinstance(files, list) or not files:
            raise RuntimeError(f"Corpus '{corpus_name}' must contain a non-empty file list.")
        if not all(isinstance(file_name, str) for file_name in files):
            raise RuntimeError(f"Corpus '{corpus_name}' contains a non-string file path.")
        normalized[corpus_name] = files
        relative_paths.extend(Path(file_name) for file_name in files)

    if len(relative_paths) != len(set(relative_paths)):
        raise RuntimeError("The upstream corpus manifest contains duplicate file paths.")

    source_data_root = (source / "sample-data").resolve()
    for relative_path in relative_paths:
        source_file = (source_data_root / relative_path).resolve()
        if (
            not source_file.is_relative_to(source_data_root)
            or relative_path.suffix.lower() != ".pdf"
            or not source_file.is_file()
        ):
            raise RuntimeError(f"Invalid or missing corpus PDF: {relative_path}")

    actual_pdfs = {
        pdf_path.relative_to(source_data_root)
        for pdf_path in (source_data_root / "pdfs").glob("*.pdf")
    }
    listed_pdfs = set(relative_paths)
    if actual_pdfs != listed_pdfs:
        missing = sorted(str(path) for path in listed_pdfs - actual_pdfs)
        unexpected = sorted(str(path) for path in actual_pdfs - listed_pdfs)
        raise RuntimeError(
            f"Corpus manifest mismatch; missing={missing or 'none'}, "
            f"unexpected={unexpected or 'none'}."
        )

    return normalized, sorted(relative_paths)


def load_json_paths(source: Path) -> list[Path]:
    """Validate and return all upstream JSON dataset files."""
    source_json_root = source / JSON_SOURCE_DIR
    if not source_json_root.is_dir():
        raise RuntimeError(f"Missing upstream JSON directory: {source_json_root}")

    json_paths = sorted(path for path in source_json_root.glob("*.json") if path.is_file())
    if not json_paths:
        raise RuntimeError("The upstream JSON directory must contain at least one .json file.")

    for json_path in json_paths:
        try:
            json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise RuntimeError(f"Invalid JSON dataset file: {json_path.name}") from error

    return [path.relative_to(source_json_root) for path in json_paths]


def synchronize(source: Path) -> None:
    """Replace the tracked snapshot after fully validating an upstream checkout."""
    source = source.resolve()
    if git_output(source, "status", "--porcelain"):
        raise RuntimeError(f"Upstream checkout has uncommitted changes: {source}")

    commit = git_output(source, "rev-parse", "HEAD")
    repository = git_output(source, "remote", "get-url", "origin")
    manifest, relative_paths = load_manifest(source)
    json_relative_paths = load_json_paths(source)

    with tempfile.TemporaryDirectory(prefix="sample-data-sync-", dir=REPO_ROOT) as temp_name:
        staged_root = Path(temp_name) / "sample-data"
        staged_pdfs = staged_root / "pdfs"
        staged_json = staged_root / "json"
        staged_pdfs.mkdir(parents=True)
        staged_json.mkdir(parents=True)

        shutil.copy2(source / MANIFEST_PATH, staged_root / "corpora.json")
        for relative_path in relative_paths:
            shutil.copy2(
                source / "sample-data" / relative_path,
                staged_pdfs / relative_path.name,
            )

        for relative_path in json_relative_paths:
            shutil.copy2(
                source / JSON_SOURCE_DIR / relative_path,
                staged_json / relative_path.name,
            )

        provenance = {
            "repository": repository,
            "commit": commit,
            "corpora": list(manifest),
            "pdfCount": len(relative_paths),
            "jsonCount": len(json_relative_paths),
        }
        (staged_root / "provenance.json").write_text(
            json.dumps(provenance, indent=2) + "\n",
            encoding="utf-8",
        )

        if TARGET_ROOT.exists():
            shutil.rmtree(TARGET_ROOT)
        shutil.move(staged_root, TARGET_ROOT)

    print(
        "Synchronized "
        f"{len(relative_paths)} PDFs and {len(json_relative_paths)} JSON files "
        f"from {repository} at {commit}."
    )


def main() -> None:
    """Parse command-line arguments and synchronize the sample data."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"Upstream repository checkout (default: {DEFAULT_SOURCE})",
    )
    arguments = parser.parse_args()
    synchronize(arguments.source)


if __name__ == "__main__":
    main()