#!/bin/sh
set -eu

echo "Writing local development settings..."
uv run --locked python infra/setup-env.py

if [ ! -f sample-data/corpora.json ] || [ ! -f sample-data/provenance.json ]; then
    echo "The tracked sample-data snapshot is missing or incomplete."
    echo "Run 'uv run python scripts/sync_sample_data.py' and commit the result."
    exit 1
fi

echo "Creating the Search index and knowledge base..."
uv run --locked python infra/create-search-indexes.py

echo "Creating the Foundry toolbox..."
uv run --locked python infra/create-toolbox-foundryiq.py

echo "Postprovision setup complete."
