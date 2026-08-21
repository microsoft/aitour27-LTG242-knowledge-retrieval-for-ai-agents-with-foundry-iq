$ErrorActionPreference = "Stop"

Write-Host "Writing local development settings..."
uv run --locked python infra/setup-env.py

if (-not (Test-Path "sample-data/corpora.json") -or
    -not (Test-Path "sample-data/provenance.json")) {
    Write-Error "The tracked sample-data snapshot is missing or incomplete. Run 'uv run python scripts/sync_sample_data.py' and commit the result."
}

Write-Host "Creating the Search index and knowledge base..."
uv run --locked python infra/create-search-indexes.py

Write-Host "Creating the Foundry toolbox..."
uv run --locked python infra/create-toolbox-foundryiq.py

Write-Host "Postprovision setup complete."
