$ErrorActionPreference = "Stop"

if (-not (Test-Path "sample-data/corpora.json") -or
    -not (Test-Path "sample-data/provenance.json")) {
    Write-Error "The tracked sample-data snapshot is missing or incomplete. Run 'uv run python scripts/sync_sample_data.py' and commit the result."
}

Write-Host "Uploading sourcing documents and applying Entra ACLs..."
uv run --locked python infra/setup-kb2-acls.py

Write-Host "Creating the Search index and knowledge base..."
uv run --locked python infra/create-search-indexes.py

Write-Host "Creating PostgreSQL schema for MCP tools..."
./scripts/setup_postgres_database.ps1

Write-Host "Granting the MCP managed identity read-only PostgreSQL access..."
./scripts/setup_postgres_azurerole.ps1

Write-Host "Loading PostgreSQL ontology and supplier seed data..."
./scripts/setup_postgres_seeddata.ps1

Write-Host "Creating the Foundry toolbox..."
uv run --locked python infra/create-toolbox-foundryiq.py

Write-Host "Postprovision setup complete."
