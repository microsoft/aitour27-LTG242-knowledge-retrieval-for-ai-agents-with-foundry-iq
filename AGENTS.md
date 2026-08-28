# Repository guidance

This project was built with the microsoft-foundry skill. Before working on or answering questions about Foundry agents, read the microsoft-foundry skill first.

The files under `sample-data/` are a synchronized snapshot from
[`pamelafox/aitour27-caldova-data`](https://github.com/pamelafox/aitour27-caldova-data).
Do not edit them directly. Make sample-data changes in the upstream repository,
then run this repository's sync script and commit the refreshed snapshot and
provenance file together.

## Changing sample data

- Make source-data, generator, template, and generated-artifact changes in a
  checkout of `pamelafox/aitour27-caldova-data`, usually at
  `../aitour27-caldova-data`.
- Change the structured source of truth rather than editing generated HTML or
  PDFs. Regenerate only the affected artifacts with the upstream repository's
  existing generation scripts.
- Keep related evidence consistent. When a shared fact changes, check every
  invoice, certificate, report, diagram, and JSON record that refers to it.
- Validate the generated output upstream, including extracted PDF text and
  layout or page-count expectations. Avoid unrelated generated-file churn.
- Commit the complete upstream change before synchronizing. The sync script
  rejects a dirty upstream checkout and records its exact `HEAD` in provenance.

## Synchronizing sample data

From this repository's root, with a clean and committed upstream checkout, run:

```bash
uv run --locked python scripts/sync_sample_data.py --source ../aitour27-caldova-data
```

Then:

- Confirm `sample-data/provenance.json` names the intended upstream repository
  and commit.
- Review all changes under `sample-data/`, especially the corpus manifest,
  generated PDFs, structured JSON, counts, and unexpected deletions.
- Run the checks relevant to the consuming code or retrieval scenario.
- Commit the refreshed `sample-data/` snapshot and provenance file together.

## Updating Python dependencies

This repository has separate Python projects and dependency files:

- The repository root project uses `pyproject.toml` and `uv.lock` for
  infrastructure scripts.
- The hosted agent uses `src/agent-toolbox-foundryiq/pyproject.toml` and
  `src/agent-toolbox-foundryiq/uv.lock`.
- The hosted agent's `requirements.txt` is a generated production export used
  by the deployment build. It must be updated when the agent dependencies
  change.
- The PostgreSQL MCP service keeps its deployment dependencies in
  `src/postgres-mcp/requirements.txt`.

When changing hosted-agent dependencies, run from the agent directory:

```bash
cd src/agent-toolbox-foundryiq
uv lock
uv export --locked --no-dev --no-emit-project \
  --format requirements-txt --output-file requirements.txt
cd ../..
```

Review and commit both the agent lockfile and exported requirements when they
change. `azd deploy <agent-name>` consumes the existing `requirements.txt`; it
does not run `uv export` or update dependency files automatically. Redeploy the
changed hosted agent after updating the export.

## Search ingestion constraints

- Keep semantic Content Understanding chunks at `maximumLength: 2000` unless
  retrieval over the certificate of analysis has been revalidated. At 500
  tokens, its analytical table splits across fragments and retrieval can omit
  rows; the demo depends on retrieving all 33 tests without gaps or duplicates.
- The pinned `azure-search-documents==12.1.0b1` models do not expose the
  `modelName` and `modelDeployment` properties required by the Content
  Understanding skill. Create or update that skillset through the Search
  client's authenticated `send_request` method with a `2026-05-01-preview`
  payload. Continue using typed SDK models for supported Search resources.
- Replace the REST payload only after a newer SDK exposes both properties and
  its serialized request has been verified.

## Open issues

### Reranker scores for remote knowledge sources

- A direct retrieval from `supplier-intelligence-kb` returned
  `rerankerScore: 0` for an included MCP reference while indexed document
  references received nonzero scores.
- Microsoft Learn documents `reranker_score: float | None` on both the base
  `KnowledgeBaseReference` and `KnowledgeBaseMcpServerReference`. It does not
  explain when an MCP or other remote-source score is calculated, omitted, or
  returned as zero.
- Do not state that remote results are never reranked or compare their zero
  scores with Search index scores. Describe `0` only as the value observed in
  the specific retrieval response.
- Recheck the service behavior and Microsoft Learn documentation as the
  knowledge-bases API and `azure-search-documents` preview evolve.
