#!/bin/sh
set -eu

echo "Writing local development settings..."
uv run --locked python infra/setup-env.py

if find data -type f -path '*/pdf/*.pdf' -print -quit | grep -q .; then
    echo "Creating the Search index and knowledge base..."
    uv run --locked python infra/create-search-indexes.py

    echo "Creating the Foundry toolbox..."
    uv run --locked python infra/create-toolbox-foundryiq.py
else
    echo "Skipping Search and toolbox setup because no Stage 1 PDFs were found."
    echo "Add PDFs under data/<document-type>/pdf/ and rerun this hook."
fi

echo "Postprovision setup complete."
