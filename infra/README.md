# Infrastructure

The infrastructure scripts provision the Foundry project, Azure AI Search,
Storage, monitoring, PostgreSQL, the PostgreSQL MCP Container App, hosted agent,
knowledge base, and toolbox used by the session.

The PostgreSQL MCP service uses a user-assigned managed identity for Entra token
authentication to Azure Database for PostgreSQL. Postprovision creates a matching
read-only database role, loads the ontology and supplier data, and registers the
service's `/mcp` URL as a knowledge source on the Foundry IQ knowledge base.

## Sample-data input

Search ingestion reads the tracked [`../sample-data/corpora.json`](../sample-data/corpora.json)
manifest and PDFs under [`../sample-data/pdfs/`](../sample-data/pdfs). The
current `session-documents` index selects the 25-file `invoice-investigation`
group. Future indexes can select `procurement` or `policy-and-diagrams` without
changing how sample data is synchronized.

[`../sample-data/provenance.json`](../sample-data/provenance.json) records the
authoritative upstream repository and commit. Normal provisioning does not need
the upstream repository checkout.

To refresh the tracked snapshot after a reviewed upstream change, run from the
repository root:

```bash
uv run --locked python scripts/sync_sample_data.py --source ../aitour27-caldova-data
```

The sync fails if the upstream checkout is dirty, a manifest path is missing or
duplicated, or a PDF exists outside the manifest.
