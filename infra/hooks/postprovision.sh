#!/bin/sh
set -eu

echo "Writing local development settings..."
uv run --locked python infra/setup-env.py

if [ -f data/index-data/documents.jsonl ]; then
    echo "Creating the Search index and knowledge base..."
    uv run --locked python infra/create-search-indexes.py

    echo "Creating the Foundry toolbox..."
    uv run --locked python infra/create-toolbox-foundryiq.py
else
    echo "Skipping Search and toolbox setup because data/index-data/documents.jsonl is a placeholder."
    echo "Add the session data and rerun this hook to finish knowledge setup."
fi

echo "Postprovision setup complete."
