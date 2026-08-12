$ErrorActionPreference = "Stop"

Write-Host "Writing local development settings..."
uv run --locked python infra/setup-env.py

if (Test-Path "data/index-data/documents.jsonl") {
    Write-Host "Creating the Search index and knowledge base..."
    uv run --locked python infra/create-search-indexes.py

    Write-Host "Creating the Foundry toolbox..."
    uv run --locked python infra/create-toolbox-foundryiq.py
} else {
    Write-Host "Skipping Search and toolbox setup because data/index-data/documents.jsonl is a placeholder."
    Write-Host "Add the session data and rerun this hook to finish knowledge setup."
}

Write-Host "Postprovision setup complete."
