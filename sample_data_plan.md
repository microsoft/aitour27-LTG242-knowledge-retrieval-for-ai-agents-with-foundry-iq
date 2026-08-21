# Sample data migration and sync plan

## Goal

Make [`pamelafox/aitour27-caldova-data`](https://github.com/pamelafox/aitour27-caldova-data)
the only source of truth for Caldova sample data. This session repository should
keep the Foundry infrastructure, Search ingestion, toolbox, hosted agent,
evaluations, session instructions, and delivery material, but should not keep a
second copy of generated documents, structured data, generation templates, or
Fabric definitions.

The sample-data repository was reviewed at commit
`7f9d83bcd7a1647d5c23ecc7ccdd5becb912dea5`.

## What is duplicated today

| This repository | Sample-data repository | Decision |
| --- | --- | --- |
| `data/**/pdf/*.pdf` | `sample-data/pdfs/*.pdf` | Use the sample-data repository. Its 37 finished PDFs are intentionally flat. |
| `data/**/source/*.json` | `sample-data/json/*.json` | Use the sample-data repository. It has the eight migrated scenario files plus `suppliers.json`, `supplier-kpi-profiles.json`, and `medicinal-product-ontology.json`. |
| `data/**/{templates,assets,html,logos}` | `generation/**` | Use the sample-data repository for all authoring and regeneration. |
| `scripts/generate_*.py` | `generation/scripts/generate_*.py` | Use the sample-data repository. |
| `FabricExport/` | `sample-data/fabric/` and `provision/fabric/` | Use the sample-data repository. It contains the current definitions and provisioning workflow. |
| `data/README.md` and `data/template-references.md` | `README.md`, `generation/README.md`, and `generation/template-references.md` | Link to the upstream documentation instead of maintaining local copies. |
| `data/index-data/` | No direct equivalent | Remove after confirming it is unused. The active Search provisioning code does not read it. |

The local `data/` tree and upstream `sample-data/pdfs/` each contain 37 PDFs,
but they are not the same corpus. The 25 invoice-investigation PDFs have stable
filenames. Nine procurement files changed supplier identities:

| Current session data | Current sample-data source |
| --- | --- |
| `RSP-ANN-2026-01.pdf` | `RSP-AST-2026-01.pdf` |
| `RSP-KRI-2026-01.pdf` | `RSP-SUM-2026-01.pdf` |
| `RSP-SAB-2026-01.pdf` | `RSP-ATL-2026-01.pdf` |
| `MSA-CAL-ANN-2024-011.pdf` | `MSA-CAL-AST-2024-011.pdf` |
| `MSA-CAL-KRI-2024-017.pdf` | `MSA-CAL-SUM-2024-017.pdf` |
| `MSA-CAL-SAB-2025-004.pdf` | `MSA-CAL-ATL-2025-004.pdf` |
| `AMD-MSA-KRI-2026-01.pdf` | `AMD-MSA-SUM-2026-01.pdf` |
| `PO-CAL-KRI-2026-1108.pdf` | `PO-CAL-SUM-2026-1108.pdf` |

`RFP-CAL-OSD-2026-01.pdf` keeps its filename but belongs to the revised bidder
set, so it must not be assumed to be unchanged. The Fabric model also changed
from the local `EnterpriseVendorModel`/`VendorSM` assets to the upstream
`SupplierSM` model and canonical supplier registry. These are content migrations,
not mechanical path changes.

## Recommended dependency model

Commit a generated runtime snapshot under `sample-data/` in this repository.
Copy all finished PDF corpora that this session may index, but not the upstream
generation sources, templates, previews, provisioning scripts, or complete
Fabric export.

- Add `sample-data/corpora.json` and `sample-data/pdfs/` containing all 37 PDFs
  listed across its three corpus groups.
- Add `sample-data/provenance.json` containing the upstream repository URL,
  commit SHA, and copied corpus names.
- Add a maintainer script, such as `scripts/sync_sample_data.py`, that copies the
  manifest-listed files from a local upstream checkout into a temporary folder,
  validates the complete set, then replaces the tracked snapshot.
- Let the sync script accept an explicit upstream checkout path and default to
  `../aitour27-caldova-data` for local development.
- Make all provisioning, CI, lab, and evaluation code read only from this
  repository's `sample-data/` directory.
- Document in `AGENTS.md` that sample-data edits belong in the upstream
  repository and must arrive here only through the sync script.

This makes every clone of the session repository self-contained and avoids
cross-repository paths during provisioning. The tradeoff is intentional
duplication of the 37 runtime PDFs. The provenance file and deterministic sync
script prevent that snapshot from becoming an independently maintained copy.

## Migration steps

### 1. Define the upstream consumption contract

The sample-data repository now contains
[`sample-data/corpora.json`](https://github.com/pamelafox/aitour27-caldova-data/blob/main/sample-data/corpora.json)
with three named groups of relative PDF paths:

- `invoice-investigation`: 25 PDFs
- `procurement`: 9 PDFs
- `policy-and-diagrams`: 3 PDFs

The manifest belongs upstream because corpus membership is a property of the
data. The local sync script should copy the manifest and every file it lists; it
should not hard-code filenames. Each Search index can then select its own named
group from the committed manifest. The upstream Git commit versions the
manifest contents.

### 2. Add the synchronization workflow

Add `scripts/sync_sample_data.py` with this contract:

1. Accept `--source <path>` pointing to an `aitour27-caldova-data` checkout,
  defaulting to `../aitour27-caldova-data`.
2. Require a clean, identifiable upstream Git commit and record its SHA.
3. Read and validate `sample-data/corpora.json`.
4. Copy the manifest and all 37 PDFs it lists into a temporary directory.
5. Reject missing, duplicate, or unexpected files before changing the tracked
  snapshot.
6. Replace `sample-data/pdfs/` only after validation succeeds.
7. Write `sample-data/provenance.json` in the same operation.

The script should not clone, pull, or modify the upstream checkout. Maintainers
choose and review the upstream revision before running it. This keeps network
and Git policy outside the copy operation and makes the resulting repository
diff easy to review.

### 3. Update Search provisioning

Change `infra/create-search-indexes.py` to:

1. Read the committed `sample-data/provenance.json` and
  `sample-data/corpora.json`.
2. Select `invoice-investigation` and require all 25 named PDFs.
3. Upload that group from `sample-data/pdfs/` under stable blob names such as
   `kb1/<filename>`.
4. Print the upstream commit SHA and corpus name used for the upload.

Do not preserve the current five-directory assumptions. They are internal to
the old local layout and no longer describe the upstream package. Future Search
indexes should select `procurement` or `policy-and-diagrams` from the same
committed manifest rather than introducing new copy rules.

### 4. Update provisioning hooks

Change both post-provision hooks to validate the committed snapshot and
provenance file instead of searching `data/*/pdf/`:

- `infra/hooks/postprovision.sh`
- `infra/hooks/postprovision.ps1`

If the snapshot is absent or incomplete, fail with one actionable message that
instructs maintainers to run the sync script. Do not silently skip Search and
toolbox setup when the session requires the corpus.

### 5. Align session content with the upstream data model

Before deleting local data, decide that the revised Aster/Summit/Atlas supplier
set and `SupplierSM` model are authoritative for this session. Then update:

- `questions.md`, especially `EnterpriseVendorModel`, `VendorSM`, and the
  Kristos-specific federated question;
- `PLAN.MD`, including the old `data/**/pdf/` ingestion path;
- `caldova.md`, including the old `FabricExport/` description and vendor model;
- attendee and delivery instructions that name local data paths or old Fabric
  artifacts.

Keep evaluation ground truth unchanged only where the 25-document corpus still
supports it. Re-run the focused retrieval evaluations after reindexing from the
upstream checkout.

### 6. Remove old local copies

After provisioning succeeds from the new committed snapshot, remove:

```text
data/
FabricExport/
scripts/generate_complex_diagrams.py
scripts/generate_gmp_inspection_report.py
scripts/generate_invoice.py
scripts/generate_operational_reports.py
scripts/generate_procurement_documents.py
scripts/generate_purchasing_policy.py
scripts/generate_quality_certificate.py
scripts/generate_temperature_reports.py
copy_data_plan.md
```

Keep `scripts/quality_eval.py` and `scripts/sync_sample_data.py`; they are
session-specific. Remove Jinja2 and Playwright from the root `pyproject.toml` if
no remaining session code imports them, then refresh the dependency lock file.
Do not copy upstream JSON, Fabric exports, generation code, or documentation
back into this repository. The manifest and its 37 listed PDFs are the only
intentional vendored data.

### 7. Document setup

Add a short sample-data section to the root README and infrastructure guide.
Normal users need no separate data setup because the required PDFs are tracked.
Document the maintainer refresh command separately:

```bash
uv run python scripts/sync_sample_data.py --source ../aitour27-caldova-data
```

Link to the upstream README for inventories, generation, provenance, and Fabric
provisioning. This repository should document only how the session consumes the
package.

## Ongoing update process

Use this sequence whenever the sample data changes:

1. Fetch the sample-data repository and review the commits between the currently
   pinned SHA and the proposed SHA.
2. Validate the upstream corpus manifest and confirm all session-required PDFs
   exist.
3. Review renamed identifiers, supplier identities, question answers, Fabric
   artifact names, and schema changes. Treat these as session content changes.
4. Check out the reviewed upstream commit and run `scripts/sync_sample_data.py`.
5. Review and commit the PDF changes and `sample-data/provenance.json` together.
6. Provision a disposable or development environment from the refreshed local
  snapshot.
7. Run the session's focused retrieval evaluations and manually check the key
   demo questions.
8. Merge the snapshot update only after the session content and evaluations
  agree with the new corpus.

Avoid scheduled copying or an automatic latest-branch sync. The clean sync unit
is a reviewed upstream commit, and the provenance update is the audit trail.

## Validation checklist

- A clean clone contains `corpora.json` and all 37 listed PDFs without requiring
  the upstream repository.
- `sample-data/provenance.json` identifies the upstream URL, commit, and copied
  corpora.
- Running the sync script twice from the same upstream commit produces no diff.
- Provisioning succeeds without an external checkout; no old `data/` or
  `FabricExport/` directory exists.
- Exactly the 25 invoice-investigation PDFs are uploaded to the `kb1` prefix.
- Future indexes can select the procurement and policy/diagram groups without
  changing the synchronization workflow.
- Removed upstream documents do not leave stale blobs or Search chunks.
- The hosted agent answers the existing four response-completeness cases from
  the newly indexed corpus.
- `questions.md`, `PLAN.MD`, and `caldova.md` use the current supplier and Fabric
  names.
- The root Python environment contains only session provisioning and evaluation
  dependencies.
- A repository-wide search finds no active references to `data/**/pdf/`,
  `FabricExport/`, `EnterpriseVendorModel`, `VendorSM`, or local generation
  scripts.
