# KB 2 ACL implementation plan

## Goal

Implement the KB 2 confidential sourcing demo from `PLAN.MD`:

- Upload the nine procurement PDFs, purchasing policy, and evidence map to an
  ADLS Gen2 container with hierarchical namespace enabled.
- Apply Microsoft Entra group-based POSIX-like ACLs to the source hierarchy.
- Ingest the content and effective permission metadata with an Azure AI Search
  ADLS Gen2 indexer.
- Enforce document-level access at retrieval time with the caller's Entra
  token, so the full corpus remains indexed while the logged-in speaker can
  retrieve only one supplier's permitted evidence.
- Create the corresponding Foundry IQ knowledge source, knowledge base, and
  Sourcing Review Agent wiring without changing KB 1 or KB 3 behavior.

## Confirmed design

The three Microsoft Learn pages support the following native preview path:

1. Use the `2026-05-01-preview` Search REST API (or an SDK version that exposes
   the same permission-filter properties).
2. Use an ADLS Gen2 data source with `indexerPermissionOptions` set to the
   required `userIds` and `groupIds` values. Include `rbacScope` only if the
   demo intentionally relies on container-level RBAC as well as ACLs.
3. Enable `permissionFilterOption` on the target index and define one
   filterable string field for each permission type. Permission fields should
   be non-retrievable after validation.
4. Pass the end-user Microsoft Entra access token in
  `x-ms-query-source-authorization` for direct Search queries. Configure the
  Foundry Toolbox connection used by the agent with `user-entra-token` and the
  appropriate audience so Foundry forwards the signed-in user's identity to
  the downstream tool. Do not use the repository's current
  `ProjectManagedIdentity` connection for the ACL-sensitive agent path.
5. Use Microsoft Entra object IDs for ACL entries, preferably group IDs rather
   than individual users. Do not use UPNs or email addresses.
6. Give the Search service managed identity `Storage Blob Data Reader` on the
   ADLS account. Give the provisioning/query identities the least Search and
   Storage roles needed for their operations.
7. Establish root read/execute ACLs and default ACLs, propagate them through
   existing directories/files, then remove access from supplier-specific paths
   as appropriate.
8. Re-run or resync permission metadata after ACL or group-membership changes;
   source changes are not reflected in the index automatically. Configure
   deletion tracking before the first indexer run.

Important preview constraints:

- Azure AI Search must have role-based access enabled and be Basic tier or
  higher. The repository's default Standard tier satisfies the tier minimum.
- The Azure portal does not configure this feature; use authenticated REST
  calls or a supported preview SDK.
- `owning users`, `owning groups`, and `Other`/`all` ACL categories are not
  supported by the ADLS Gen2 permission-ingestion preview. Use named users and
  named groups.
- Knowledge-source ACL ingestion cannot be combined with an asset store, so
  image serving is not part of this KB 2 design.
- Permission changes have synchronization lag. The demo must validate the
  indexed permission state, not assume an immediate source-to-index update.

## Proposed source layout and ACL model

Use a dedicated HNS-enabled storage account and a dedicated container for KB 2
so the existing blob account and KB 1 prefix remain unchanged. Suggested
layout:

```text
kb2-sourcing/
  shared/CAL-POL-PUR-001.pdf
  shared/RFP-CAL-OSD-2026-01.pdf
  evaluator/RSP-AST-2026-01.pdf
  evaluator/RSP-SUM-2026-01.pdf
  evaluator/RSP-ATL-2026-01.pdf
  evaluator/MSA-CAL-AST-2024-011.pdf
  evaluator/MSA-CAL-SUM-2024-017.pdf
  evaluator/MSA-CAL-ATL-2025-004.pdf
  evaluator/AMD-MSA-SUM-2026-01.pdf
  evaluator/PO-CAL-SUM-2026-1108.pdf
  shared/CAL-MAP-EVD-001.pdf
```

The exact folder layout must follow ADLS hierarchical permission inheritance.
The broader production access model is:

| Principal/group | Access |
| --- | --- |
| Procurement evaluation group | All 11 documents |
| Finance/executive group | Shared policy/RFP, evaluation evidence, agreements, amendment, and purchase order; no bidder responses unless explicitly granted |
| Aster Ridge group | Shared policy/RFP, Aster Ridge response, and Aster Ridge agreement |
| Summit Dose group | Shared policy/RFP, Summit Dose response, and Summit Dose agreement, plus intentionally shared award documents |
| Atlas Regional group | Shared policy/RFP, Atlas Regional response, and Atlas Regional agreement |

Prefer existing Entra security-group object IDs when they can be discovered
safely. Select one group that contains the provisioning user and one group that
does not contain the user. Put the member group in `groupIds` for the Summit
Dose files and the non-member group in `groupIds` for the other bidder files.
The user's unchanged token then demonstrates group-based trimming without
creating users, groups, or membership changes. Keep the discovered IDs in an
environment variable or a local, ignored configuration file; never commit
tenant-specific identifiers. Fall back to the provisioning user's direct OID
in `userIds` if suitable groups cannot be selected.

For the talk, treat the speaker as a Summit Dose representative. Grant the OID
read access to the shared policy, RFP, evidence map, Summit Dose response, and
Summit Dose agreement. Do not grant it access to the Aster Ridge or Atlas
Regional responses/agreements, the amendment, the purchase order, or other
confidential evaluation material.

## Implementation stages

### 1. Confirm identity and resource choices

- Provision a new HNS-enabled ADLS Gen2 account and dedicated KB 2 container.
- Discover two existing security-enabled Entra groups: one containing the
  provisioning user and one not containing the user. No group creation or
  membership changes are required.
- Use an administrative Search view to show the complete corpus, and the
  delegated agent query to show the restricted corpus visible to that user.
- Configure and validate the Foundry Toolbox connection for managed user
  identity passthrough (`user-entra-token`). The Toolbox handles the delegated
  token flow server-side; the agent should not implement an OAuth client, token
  exchange, or on-behalf-of flow itself.

### 2. Add infrastructure

Update the infrastructure to provision or reference:

- A new HNS-enabled ADLS Gen2 storage account and private/no-public container
  for KB 2.
- Search-service managed identity access to read blobs and ACL metadata.
- The required Search RBAC assignments and any storage role assignments for the
  provisioning identity.
- Outputs for the account, filesystem/container, and resource ID needed by the
  provisioning script.

Keep the existing KB 1 storage connection and `knowledge` container stable.
Do not grant supplier principals access to the Search service itself; they need
query access through the application/agent identity while document access is
decided by the forwarded source token.

### 3. Add upload and ACL provisioning

Extend or add a focused script that:

- Reads the `procurement` and `policy-and-diagrams` entries in
  `sample-data/corpora.json` and verifies the expected 11 PDFs.
- Uploads only those committed PDFs to the KB 2 ADLS container.
- Creates directories before files so ACL inheritance is deterministic.
- Discovers or accepts a member-group OID and a non-member-group OID, then
  applies the member group to the shared files and Summit Dose files and the
  non-member group to the other bidder files. It leaves both groups off
  confidential evaluation files unless explicitly required, and recursively
  propagates the intended ACLs to existing content.
- Rejects mail-enabled or non-security-enabled groups, avoids groups with
  obviously broad names such as `All Company`, and supports the direct-user-OID
  fallback when no suitable pair exists.
- Logs paths and counts, but never logs access tokens or secrets.

Because `sample-data/` is synchronized generated content, do not modify the
PDFs or JSON files in this repository for ACL work.

### 4. Create the ACL-aware Search pipeline

Add a separate KB 2 index and ADLS Gen2 indexer payload using the preview REST
API already used by `infra/create-search-indexes.py`:

- ADLS Gen2 data source with a ResourceId connection and
  `indexerPermissionOptions: ["userIds", "groupIds"]` (plus `rbacScope` only
  if selected in stage 1).
- Index fields for `UserIds` and `GroupIds` as `Collection(Edm.String)`,
  `filterable: true`, with the corresponding `permissionFilter` values.
- `permissionFilterOption: "enabled"`.
- Explicit field mappings from ADLS metadata fields
  `metadata_user_ids`/`metadata_group_ids` to the permission fields.
- Content extraction, chunking, embeddings, and index projections compatible
  with the KB 2 question. If chunks are projected, confirm permission metadata
  is copied to every chunk; otherwise ACL enforcement can be bypassed by a
  chunk-level result.
- Deletion tracking enabled before the first run.

Keep permission fields retrievable during development only long enough to
inspect a sample document, then set them to non-retrievable.

### 5. Create the Foundry IQ knowledge base

- Create a KB 2 Search-index knowledge source over the ACL-aware index.
- Create the Sourcing Review knowledge base with a distinct name and the same
  retrieval model/output conventions used by KB 1.

### 6. Create the Sourcing Review Agent

- Add a third scenario configuration to the existing hosted agent entry point
  in `src/agent-toolbox-foundryiq/main.py`, selected through `AGENT_SCENARIO`.
  The configuration should provide a distinct agent name, toolbox name, and
  sourcing-specific instructions.
- Add a Sourcing Review toolbox containing the ACL-aware Azure AI Search or
  knowledge-base tool and Code Interpreter. Keep the inner Search/knowledge
  source connection appropriate for the resource, but expose the Toolbox
  endpoint to the agent through a project connection configured as
  `user-entra-token` with audience `https://ai.azure.com`.
- Use the hosted-agent `FoundryToolbox` integration already present in
  `src/agent-toolbox-foundryiq/main.py`; do not add custom token forwarding,
  OAuth client code, or an on-behalf-of implementation to the agent.
- Instruct the agent to use only retrieved, ACL-filtered evidence and to say it
  cannot make a complete comparison when competitor bids are unavailable.
- Ensure Code Interpreter receives only the filtered retrieved facts. Prefer a
  weighted-score table for the stage demo because generated chart artifacts do
  not currently render in the Foundry playground.

Agent instructions should explicitly require that the agent:

- Use the sourcing knowledge-base tool before answering.
- Treat the retrieved result set as the complete evidence available to the
  current caller; never infer inaccessible bidders or evaluation scores.
- Cite each material claim with the retrieved document title and page number
  when available.
- State that it cannot make a complete bidder comparison when the caller lacks
  competitor documents.
- Pass only retrieved, authorized values to Code Interpreter and return a
  weighted-score Markdown table rather than relying on an image artifact.

The deployment and runbook must set `AGENT_SCENARIO=sourcing-review` for the
demo and use the Toolbox consumer endpoint. Use a version-specific Toolbox
endpoint only while validating a new version, then promote the verified version
before rehearsal.

### 7. Validate authorization end to end

Run the identical question through two views:

1. Azure AI Search administrative view: use Search Explorer or an equivalent
  admin-key/index-inspection path to show that the index contains all 11
  source documents. This demonstrates corpus completeness, not end-user
  authorization.
2. Logged-in Sourcing Review Agent: run the bidder-comparison question with the
  speaker's delegated authorization context through the hosted agent and its
  `user-entra-token` Toolbox connection. Only the user's permitted
  evidence may be grounded; inaccessible competitor documents and confidential
  evaluation evidence must be absent, and the agent must explicitly report
  when it cannot make a complete comparison.

There is only one speaker/test user, so this is not a two-user comparison. The
portal view demonstrates index completeness, while the agent view demonstrates
that the same signed-in user's token trims retrieval results.

The demo should not depend on changing group membership during the talk. Azure
AI Search can cache group-membership checks for a short period, so membership
switching is unsuitable for a deterministic stage demonstration. Instead, use
a preconfigured logged-in principal with a stable ACL/token context and a
`user-entra-token` Toolbox connection.

Also verify:

- The administrative Search view shows all 11 indexed documents, while the
  logged-in agent or authenticated retrieval client sees only authorized
  documents.
- A direct Search request with the end-user token returns a trimmed document set
  when `x-ms-query-source-authorization` is present.
- Requests without the required source authorization are rejected or do not
  expose protected documents, according to the preview behavior observed.
- Index permission fields contain the expected group object IDs during
  development, and the signed-in user's token contains the member group claim.
- A permission change followed by the documented resync/reset mechanism changes
  retrieval results as expected.
- Deleted source PDFs disappear from the index after an indexer run.
- Citations never expose inaccessible documents through filenames, snippets,
  traces, or Code Interpreter inputs.

## Likely files to change

- `infra/main.bicep`
- `infra/core/storage/storage.bicep` or a new KB 2 storage module
- `infra/core/search/azure_ai_search.bicep`
- `infra/create-search-indexes.py` or a new focused KB 2 provisioning script
- `infra/setup-env.py`
- `infra/postdeploy.py`
- `infra/create-toolbox-foundryiq.py`
- `src/agent-toolbox-foundryiq/main.py`
- `.env.example` if the repository adds one

Do not edit `sample-data/` directly. Do not change validation scripts until the
implementation contract is confirmed.

## Resolved implementation decisions

- Use `https://ai.azure.com` as the audience for the `user-entra-token`
  connection to the Foundry Toolbox endpoint. No separate OAuth application
  registration is required for this managed user-token passthrough path.
- Discover an existing security-enabled group that contains the provisioning
  user and another that does not. Use their object IDs in `groupIds` for the
  restricted demo corpus. Fall back to the provisioning user's direct OID in
  `userIds` if no safe group pair is available.
- Treat the speaker as a Summit Dose representative. The speaker's group or
  user OID can access the shared policy, RFP, evidence map, Summit Dose
  response, and Summit Dose agreement, but not the other bidder or confidential
  evaluation documents.
- Document finance/executive access as a broader production model, but omit it
  from this single-speaker implementation.

## Access needed from the environment owner

Tenant-wide Entra administrator rights are not required if the directory
objects already exist. The implementation can proceed with:

- Read access to discover existing security groups and check the provisioning
  user's membership. The setup can then use the selected member and non-member
  group object IDs in `groupIds`; no directory write permission is required.
- The provisioning user's Entra object ID as a direct-user fallback if no safe
  group pair is available.
- Permission for the deployment identity to create the HNS storage account and
  container, assign the Search managed identity `Storage Blob Data Reader`, and
  grant the setup identity `Storage Blob Data Owner` on the KB 2 filesystem.
- Permission for the provisioning identity to configure the Search service and
  indexer, typically `Search Service Contributor` plus `Search Index Data
  Contributor`.

If the operator cannot assign roles, an Azure subscription/resource-group owner
or User Access Administrator must perform those role assignments once. The
operator does not need to be a tenant administrator to use the resulting
storage ACLs or run the validation queries.

## References

- [Document-Level Access Control](https://learn.microsoft.com/en-us/azure/search/search-document-level-access-overview)
- [Indexing ACLs Using the Push REST API](https://learn.microsoft.com/en-us/azure/search/search-index-access-control-lists-and-rbac-push-api)
- [Use ADLS Gen2 Indexer to Ingest Permission Metadata](https://learn.microsoft.com/en-us/azure/search/search-indexer-access-control-lists-and-role-based-access)
- [Mastering Foundry Toolbox notebook](https://github.com/microsoft-foundry/forgebook/blob/main/notebooks/mastering-foundry-toolbox.ipynb)
- [Building Agents that Act on Your Behalf with Toolboxes in Foundry](https://devblogs.microsoft.com/foundry/building-agents-that-act-on-your-behalf-with-toolboxes-in-foundry/)
- [Azure Search OpenAI demo authentication setup](https://github.com/Azure-Samples/azure-search-openai-demo/blob/main/scripts/auth_init.py)
- [Connect agents to MCP server endpoints](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/model-context-protocol)
