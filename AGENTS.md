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
