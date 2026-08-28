# Infrastructure

The infrastructure scripts provision the Foundry project, Azure AI Search,
Storage, monitoring, PostgreSQL, the PostgreSQL MCP Container App, hosted agent,
knowledge base, and toolbox used by the session.

The PostgreSQL MCP service uses a user-assigned managed identity for Entra token
authentication to Azure Database for PostgreSQL. Postprovision creates a matching
read-only database role, loads the ontology and supplier data, and registers the
service's `/mcp` URL as a knowledge source on the Foundry IQ knowledge base.
The remote source exposes only `search_products`, `search_substances`,
`search_authorizations`, and `search_manufacturers`; it does not accept
arbitrary SQL.

The sourcing-review scenario uses a separate HNS-enabled ADLS Gen2 account and
Entra group ACLs. Its `UserEntraToken` connection is scoped to
`https://search.azure.com`, so retrieval is authorized as the signed-in caller.

## Prerequisites

Install and sign in to:

- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli)
- [Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

Use an Azure subscription where you can create resources and role assignments.
The ACL-aware demo also requires two existing Microsoft Entra security groups:

- A member group containing the provisioning and demo user
- A non-member group that does not contain that user

The deployment does not create groups or change group membership.

## Configure the environment

From the repository root, create or select an azd environment. Generate a strong
shared key for the PostgreSQL MCP endpoint and store it in that environment:

```bash
azd env set MCP_API_KEY "$(openssl rand -hex 32)"
```

Find candidate Entra groups, then store the selected object IDs:

```bash
uv run python infra/find-kb2-group-oids.py
azd env set SOURCING_MEMBER_GROUP_OID <member-group-oid>
azd env set SOURCING_NON_MEMBER_GROUP_OID <non-member-group-oid>
```

⚠️ Do not commit tenant-specific group IDs or the MCP API key.

## Deploy

Run the complete deployment from the repository root:

```bash
azd up
```

In addition to provisioning Azure resources, the azd hooks:

- Load provisioned settings from the selected azd environment
- Upload the sourcing documents and apply their Entra ACLs
- Create and run the Search indexing pipelines
- Create the PostgreSQL schema, read-only identity role, and seed data
- Create the Foundry IQ knowledge bases and toolboxes
- Deploy the invoice-investigation, sourcing-review, and
  supplier-intelligence hosted agents
- Complete postdeployment registration and role assignments

### Redeploy one agent

After changing an agent's source code or system instructions, redeploy only that
agent from the repository root. Replace `<agent-name>` with the service name for
the agent you changed:

```bash
azd deploy <agent-name>
```

For example, to redeploy the invoice agent:

```bash
azd deploy invoice-investigation-agent
```

This uses the currently selected azd environment and does not rerun resource
provisioning or the postprovision and postdeploy hooks. Use `azd up` when those
steps are needed.

## ACL-aware sourcing scenario

The sourcing corpus contains 12 documents: nine procurement documents and three
policy or diagram documents. Shared documents are readable by both configured
groups. Supplier-specific documents are assigned to either the member or
non-member group.

The member group represents the Summit Dose view and can retrieve the Summit
Dose response and agreement. The non-member group can retrieve the Aster Ridge
and Atlas Regional responses and agreements. Policy and diagram documents and
the RFP are shared with both groups. The amendment and purchase order are
confidential and are not granted to either demo group.

Azure AI Search ingests the ADLS Gen2 ACL metadata into filterable,
non-retrievable `user_ids` and `group_ids` fields. The `sourcing-documents` index
has permission filtering enabled, and the `sourcing-review-kb` knowledge base
uses the caller's delegated identity when retrieving evidence.

### Validate the demo

1. In Search Explorer, query `sourcing-documents` administratively and confirm
   that all 12 documents are indexed.
2. Run the Sourcing Review Agent as the member-group user and ask: "Compare the
   technical capabilities and cost of the three bidders."
3. Confirm that the response cites only shared and Summit Dose evidence, states
   that the inaccessible bidder responses are unavailable, and does not infer
   their contents or scores.

ACL changes are not reflected in existing indexed documents automatically.
Reapply the ACLs and rerun the indexing pipeline after changing group or document
assignments.

## Rerun individual stages

The azd hooks normally run these stages. Use the commands directly when
troubleshooting an existing deployment:

```bash
# Upload sourcing documents and apply ACLs
uv run --locked python infra/setup-kb2-acls.py

# Recreate and run the Search indexing pipelines
uv run --locked python infra/create-search-indexes.py

# Recreate the Foundry IQ toolboxes
uv run --locked python infra/create-toolbox-foundryiq.py

# Repeat postdeployment registration and role assignments
uv run --locked python infra/postdeploy.py
```

If documents are missing, confirm the tracked sample-data snapshot is complete
and review the indexer status in the Azure portal. If caller-specific filtering
is wrong, verify the selected group IDs, the ADLS ACL assignments, and the
`UserEntraToken` connection before rerunning the ACL and indexing stages.

## Sample-data input

Search ingestion reads the tracked [`../sample-data/corpora.json`](../sample-data/corpora.json)
manifest and PDFs under [`../sample-data/pdfs/`](../sample-data/pdfs). The
`session-documents` index selects the 25-file `invoice-investigation` group.
The `sourcing-documents` index selects the nine-file `procurement` group and
the three-file `policy-and-diagrams` group.

Only manifest-selected PDFs are indexing inputs. Do not index the JSON source
records or any HTML previews, templates, or image assets from the upstream
sample-data repository. The Supplier Intelligence knowledge base uses a
supplier-specific knowledge source over `session-documents` together with the
remote `postgres-ontology-suppliers` MCP knowledge source; relational records
are not copied into the Search index.

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

## References

- [Azure AI Search document-level access control](https://learn.microsoft.com/azure/search/search-document-level-access-overview)
- [ADLS Gen2 indexer ACL ingestion](https://learn.microsoft.com/azure/search/search-indexer-access-control-lists-and-role-based-access)
- [Foundry MCP tool authentication](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/model-context-protocol)
