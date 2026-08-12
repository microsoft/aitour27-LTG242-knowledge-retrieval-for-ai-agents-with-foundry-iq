$ErrorActionPreference = "Stop"

Write-Host "Writing local development settings..."
uv run --locked python infra/setup-env.py

$Stage1Pdf = Get-ChildItem -Path "data" -Filter "*.pdf" -Recurse |
    Where-Object { $_.Directory.Name -eq "pdf" } |
    Select-Object -First 1

if ($Stage1Pdf) {
    Write-Host "Creating the Search index and knowledge base..."
    uv run --locked python infra/create-search-indexes.py

    Write-Host "Creating the Foundry toolbox..."
    uv run --locked python infra/create-toolbox-foundryiq.py
} else {
    Write-Host "Skipping Search and toolbox setup because no Stage 1 PDFs were found."
    Write-Host "Add PDFs under data/<document-type>/pdf/ and rerun this hook."
}

Write-Host "Postprovision setup complete."
