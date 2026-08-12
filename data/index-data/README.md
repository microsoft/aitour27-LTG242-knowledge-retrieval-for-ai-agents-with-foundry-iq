# Search index data

Copy `documents.jsonl.example` to `documents.jsonl` and replace the example
record before running `azd provision`. Each line must be a JSON object matching
`index.json`, with these fields:

- `uid`: unique document or chunk identifier
- `snippet_parent_id`: identifier shared by chunks from the same source
- `blob_path`: source path or URL
- `snippet`: searchable text

Do not include `snippet_vector`; Azure AI Search generates it with the configured
`text-embedding-3-large` vectorizer.
