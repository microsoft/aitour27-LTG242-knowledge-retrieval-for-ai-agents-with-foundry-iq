#!/bin/sh
set -eu

if [ ! -f sample-data/corpora.json ] || [ ! -f sample-data/provenance.json ]; then
    echo "The tracked sample-data snapshot is missing or incomplete."
    echo "Run 'uv run python scripts/sync_sample_data.py' and commit the result."
    exit 1
fi

echo "Uploading sourcing documents and applying Entra ACLs..."
uv run --locked python infra/setup-kb2-acls.py

echo "Creating the Search index and knowledge base..."
uv run --locked python infra/create-search-indexes.py

echo "Creating PostgreSQL schema for MCP tools..."
./scripts/setup_postgres_database.sh

echo "Granting the MCP managed identity read-only PostgreSQL access..."
./scripts/setup_postgres_azurerole.sh

echo "Loading PostgreSQL ontology and supplier seed data..."
./scripts/setup_postgres_seeddata.sh

echo "Creating the Foundry toolbox..."
uv run --locked python infra/create-toolbox-foundryiq.py

echo "Postprovision setup complete."
