# PostgreSQL MCP plan for Azure AI Search Knowledge Base

## Objective

Create a PostgreSQL-backed MCP server that exposes exactly four generic search tools for Azure AI Search Knowledge Base runtime retrieval.

Scope is limited to:

- `medicinal-product-ontology.json`
- `suppliers.json`

Tool surface is limited to:

1. `search_products`
2. `search_substances`
3. `search_authorizations`
4. `search_manufacturers`

No additional tools are included in v1.

## Why this shape

- Azure AI Search Knowledge Base tool selection is more reliable with a short, generic tool list.
- `search_*` naming aligns with retrieval/reranking behavior.
- Standardized output shape improves parsing and citation quality.
- Ontology + suppliers gives a coherent dataset with useful joins while keeping implementation small.

## Data scope and joins

## Included source files

- `sample-data/json/medicinal-product-ontology.json`
- `sample-data/json/suppliers.json`

## Join dependency

`manufacturer_active_substances.manufacturer_id` references supplier IDs (`sup-004`, etc.).
To provide human-readable manufacturer results, suppliers must be loaded.

## Excluded for v1

- `supplier-kpi-profiles.json`
- `waypoint-supplier-invoices.json`
- `procurement-chain.json`
- Other scenario JSON files

These can be added in v2 with separate `search_*` tools if needed.

## PostgreSQL schema (v1)

## Core tables

1. `medicinal_products`
- `product_id` text primary key
- `name` text not null
- `dosage_form` text
- `strength` text
- `route_of_administration` text

2. `active_substances`
- `substance_id` text primary key
- `preferred_name` text not null
- `substance_type` text

3. `regulatory_agencies`
- `agency_id` text primary key
- `name` text not null
- `abbreviation` text
- `country_or_region` text

4. `marketing_authorizations`
- `authorization_id` text primary key
- `authorization_number` text not null
- `product_id` text not null references `medicinal_products(product_id)`
- `agency_id` text not null references `regulatory_agencies(agency_id)`
- `market` text
- `status` text
- `effective_date` date null

5. `product_active_substances`
- `product_id` text not null references `medicinal_products(product_id)`
- `substance_id` text not null references `active_substances(substance_id)`
- primary key (`product_id`, `substance_id`)

6. `suppliers`
- `supplier_id` text primary key
- `supplier_name` text not null
- `service_category` text not null
- `address_lines` jsonb not null

7. `manufacturer_active_substances`
- `manufacturer_id` text not null references `suppliers(supplier_id)`
- `substance_id` text not null references `active_substances(substance_id)`
- primary key (`manufacturer_id`, `substance_id`)

8. `dataset_provenance`
- `id` smallint primary key default 1
- `upstream_repository` text not null
- `upstream_commit` text not null
- `loaded_at_utc` timestamptz not null
- `json_files` int not null

## Recommended indexes

- `medicinal_products(name)`
- `active_substances(preferred_name)`
- `marketing_authorizations(product_id, status)`
- `marketing_authorizations(agency_id, status)`
- `suppliers(service_category, supplier_name)`
- `manufacturer_active_substances(substance_id, manufacturer_id)`

Optional (for fuzzy search):

- `pg_trgm` + GIN indexes on product/substance/supplier names.

## MCP tool contract (exactly 4 tools)

All tools must return the same top-level shape:

```json
{
  "results": [],
  "total_count": 0,
  "next_skip": null
}
```

Every result item should include:

- `id` (stable identifier)
- `title` (concise display title)
- `content` (short rankable text)
- `entity_type` (product|substance|authorization|manufacturer)
- `source` (e.g., `postgres/ontology_suppliers`)
- `metadata` (small object)

## 1) search_products

Purpose:
Search medicinal products.

Inputs:
- `query` (string, optional)
- `dosage_form` (string, optional)
- `route_of_administration` (string, optional)
- `top` (int, default 10, max 50)
- `skip` (int, default 0)

Behavior:
- Text match on `name` and optionally `strength`.
- Apply optional filters.
- Return concise product summaries.

## 2) search_substances

Purpose:
Search active substances, optionally with linked products.

Inputs:
- `query` (string, optional)
- `substance_type` (string, optional)
- `include_products` (bool, default false)
- `top` (int, default 10, max 50)
- `skip` (int, default 0)

Behavior:
- Text match on `preferred_name`.
- Optional filter on `substance_type`.
- If `include_products=true`, include linked product IDs/names in metadata.

## 3) search_authorizations

Purpose:
Search marketing authorizations.

Inputs:
- `query` (string, optional; matches authorization number and product/agency names)
- `product_id` (string, optional)
- `agency_id` (string, optional)
- `market` (string, optional)
- `status` (string, optional)
- `top` (int, default 10, max 50)
- `skip` (int, default 0)

Behavior:
- Join authorizations with product and agency tables.
- Filter by provided fields.
- Return authorization-centric summaries.

## 4) search_manufacturers

Purpose:
Search ontology manufacturers (supplier-backed), optionally constrained by substance.

Inputs:
- `query` (string, optional; matches supplier name)
- `country` (string, optional)
- `substance_id` (string, optional)
- `top` (int, default 10, max 50)
- `skip` (int, default 0)

Behavior:
- Restrict suppliers to manufacturer IDs present in `manufacturer_active_substances`.
- Prefer API manufacturing suppliers.
- If `substance_id` is set, return only manufacturers linked to that substance.

## MCP implementation approach

- Build one server process with these four tools only.
- Keep tool names stable; avoid aliases.
- Keep result payload compact to reduce token overhead.
- Use parameterized SQL only.
- Enforce `top <= 50` server-side.
- Add query timeout (for example 5 seconds).

## SQL templates for 4 tools (pg_trgm and fallback)

Use parameterized SQL for all queries. The examples below assume these bound parameters where relevant:

- `:query` (text)
- `:top` (int)
- `:skip` (int)
- tool-specific filters (`:status`, `:market`, etc.)

## Enable optional fuzzy search

Run once per database (optional):

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX IF NOT EXISTS ix_products_name_trgm
  ON medicinal_products USING gin (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS ix_substances_name_trgm
  ON active_substances USING gin (preferred_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS ix_suppliers_name_trgm
  ON suppliers USING gin (supplier_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS ix_auth_number_trgm
  ON marketing_authorizations USING gin (authorization_number gin_trgm_ops);
```

Verify availability/support in an environment:

```sql
SELECT name, default_version, installed_version
FROM pg_available_extensions
WHERE name = 'pg_trgm';
```

If extension setup isn't available in an environment, use the fallback templates below.

## 1) search_products

pg_trgm variant:

```sql
SELECT
  p.product_id AS id,
  p.name AS title,
  concat_ws(' | ', p.dosage_form, p.strength, p.route_of_administration) AS content,
  'product' AS entity_type,
  'postgres/ontology_suppliers' AS source,
  jsonb_build_object(
    'product_id', p.product_id,
    'dosage_form', p.dosage_form,
    'strength', p.strength,
    'route_of_administration', p.route_of_administration,
    'score', greatest(similarity(p.name, coalesce(:query, '')), similarity(coalesce(p.strength, ''), coalesce(:query, '')))
  ) AS metadata
FROM medicinal_products p
WHERE (:query IS NULL OR :query = '' OR p.name % :query OR coalesce(p.strength, '') % :query)
  AND (:dosage_form IS NULL OR p.dosage_form = :dosage_form)
  AND (:route_of_administration IS NULL OR p.route_of_administration = :route_of_administration)
ORDER BY greatest(similarity(p.name, coalesce(:query, '')), similarity(coalesce(p.strength, ''), coalesce(:query, ''))) DESC, p.name
LIMIT :top OFFSET :skip;
```

ILIKE fallback:

```sql
SELECT
  p.product_id AS id,
  p.name AS title,
  concat_ws(' | ', p.dosage_form, p.strength, p.route_of_administration) AS content,
  'product' AS entity_type,
  'postgres/ontology_suppliers' AS source,
  jsonb_build_object(
    'product_id', p.product_id,
    'dosage_form', p.dosage_form,
    'strength', p.strength,
    'route_of_administration', p.route_of_administration
  ) AS metadata
FROM medicinal_products p
WHERE (:query IS NULL OR :query = '' OR p.name ILIKE '%' || :query || '%' OR coalesce(p.strength, '') ILIKE '%' || :query || '%')
  AND (:dosage_form IS NULL OR p.dosage_form = :dosage_form)
  AND (:route_of_administration IS NULL OR p.route_of_administration = :route_of_administration)
ORDER BY p.name
LIMIT :top OFFSET :skip;
```

## 2) search_substances

pg_trgm variant:

```sql
SELECT
  s.substance_id AS id,
  s.preferred_name AS title,
  s.substance_type AS content,
  'substance' AS entity_type,
  'postgres/ontology_suppliers' AS source,
  jsonb_build_object(
    'substance_id', s.substance_id,
    'substance_type', s.substance_type,
    'score', similarity(s.preferred_name, coalesce(:query, ''))
  ) AS metadata
FROM active_substances s
WHERE (:query IS NULL OR :query = '' OR s.preferred_name % :query)
  AND (:substance_type IS NULL OR s.substance_type = :substance_type)
ORDER BY similarity(s.preferred_name, coalesce(:query, '')) DESC, s.preferred_name
LIMIT :top OFFSET :skip;
```

ILIKE fallback:

```sql
SELECT
  s.substance_id AS id,
  s.preferred_name AS title,
  s.substance_type AS content,
  'substance' AS entity_type,
  'postgres/ontology_suppliers' AS source,
  jsonb_build_object(
    'substance_id', s.substance_id,
    'substance_type', s.substance_type
  ) AS metadata
FROM active_substances s
WHERE (:query IS NULL OR :query = '' OR s.preferred_name ILIKE '%' || :query || '%')
  AND (:substance_type IS NULL OR s.substance_type = :substance_type)
ORDER BY s.preferred_name
LIMIT :top OFFSET :skip;
```

## 3) search_authorizations

pg_trgm variant:

```sql
SELECT
  a.authorization_id AS id,
  a.authorization_number AS title,
  concat_ws(' | ', p.name, r.abbreviation, a.market, a.status) AS content,
  'authorization' AS entity_type,
  'postgres/ontology_suppliers' AS source,
  jsonb_build_object(
    'authorization_id', a.authorization_id,
    'product_id', a.product_id,
    'agency_id', a.agency_id,
    'market', a.market,
    'status', a.status,
    'effective_date', a.effective_date,
    'score', greatest(
      similarity(a.authorization_number, coalesce(:query, '')),
      similarity(p.name, coalesce(:query, '')),
      similarity(r.name, coalesce(:query, ''))
    )
  ) AS metadata
FROM marketing_authorizations a
JOIN medicinal_products p ON p.product_id = a.product_id
JOIN regulatory_agencies r ON r.agency_id = a.agency_id
WHERE (
    :query IS NULL OR :query = ''
    OR a.authorization_number % :query
    OR p.name % :query
    OR r.name % :query
  )
  AND (:product_id IS NULL OR a.product_id = :product_id)
  AND (:agency_id IS NULL OR a.agency_id = :agency_id)
  AND (:market IS NULL OR a.market = :market)
  AND (:status IS NULL OR a.status = :status)
ORDER BY greatest(
  similarity(a.authorization_number, coalesce(:query, '')),
  similarity(p.name, coalesce(:query, '')),
  similarity(r.name, coalesce(:query, ''))
) DESC, a.authorization_number
LIMIT :top OFFSET :skip;
```

ILIKE fallback:

```sql
SELECT
  a.authorization_id AS id,
  a.authorization_number AS title,
  concat_ws(' | ', p.name, r.abbreviation, a.market, a.status) AS content,
  'authorization' AS entity_type,
  'postgres/ontology_suppliers' AS source,
  jsonb_build_object(
    'authorization_id', a.authorization_id,
    'product_id', a.product_id,
    'agency_id', a.agency_id,
    'market', a.market,
    'status', a.status,
    'effective_date', a.effective_date
  ) AS metadata
FROM marketing_authorizations a
JOIN medicinal_products p ON p.product_id = a.product_id
JOIN regulatory_agencies r ON r.agency_id = a.agency_id
WHERE (
    :query IS NULL OR :query = ''
    OR a.authorization_number ILIKE '%' || :query || '%'
    OR p.name ILIKE '%' || :query || '%'
    OR r.name ILIKE '%' || :query || '%'
  )
  AND (:product_id IS NULL OR a.product_id = :product_id)
  AND (:agency_id IS NULL OR a.agency_id = :agency_id)
  AND (:market IS NULL OR a.market = :market)
  AND (:status IS NULL OR a.status = :status)
ORDER BY a.authorization_number
LIMIT :top OFFSET :skip;
```

## 4) search_manufacturers

pg_trgm variant:

```sql
SELECT
  s.supplier_id AS id,
  s.supplier_name AS title,
  concat_ws(' | ', s.service_category, s.address_lines->>2) AS content,
  'manufacturer' AS entity_type,
  'postgres/ontology_suppliers' AS source,
  jsonb_build_object(
    'supplier_id', s.supplier_id,
    'service_category', s.service_category,
    'country', s.address_lines->>2,
    'substance_ids', (
      SELECT jsonb_agg(mas.substance_id ORDER BY mas.substance_id)
      FROM manufacturer_active_substances mas
      WHERE mas.manufacturer_id = s.supplier_id
    ),
    'score', similarity(s.supplier_name, coalesce(:query, ''))
  ) AS metadata
FROM suppliers s
WHERE EXISTS (
    SELECT 1
    FROM manufacturer_active_substances mas0
    WHERE mas0.manufacturer_id = s.supplier_id
  )
  AND (:query IS NULL OR :query = '' OR s.supplier_name % :query)
  AND (:country IS NULL OR s.address_lines->>2 = :country)
  AND (
    :substance_id IS NULL
    OR EXISTS (
      SELECT 1
      FROM manufacturer_active_substances mas1
      WHERE mas1.manufacturer_id = s.supplier_id
        AND mas1.substance_id = :substance_id
    )
  )
ORDER BY similarity(s.supplier_name, coalesce(:query, '')) DESC, s.supplier_name
LIMIT :top OFFSET :skip;
```

ILIKE fallback:

```sql
SELECT
  s.supplier_id AS id,
  s.supplier_name AS title,
  concat_ws(' | ', s.service_category, s.address_lines->>2) AS content,
  'manufacturer' AS entity_type,
  'postgres/ontology_suppliers' AS source,
  jsonb_build_object(
    'supplier_id', s.supplier_id,
    'service_category', s.service_category,
    'country', s.address_lines->>2,
    'substance_ids', (
      SELECT jsonb_agg(mas.substance_id ORDER BY mas.substance_id)
      FROM manufacturer_active_substances mas
      WHERE mas.manufacturer_id = s.supplier_id
    )
  ) AS metadata
FROM suppliers s
WHERE EXISTS (
    SELECT 1
    FROM manufacturer_active_substances mas0
    WHERE mas0.manufacturer_id = s.supplier_id
  )
  AND (:query IS NULL OR :query = '' OR s.supplier_name ILIKE '%' || :query || '%')
  AND (:country IS NULL OR s.address_lines->>2 = :country)
  AND (
    :substance_id IS NULL
    OR EXISTS (
      SELECT 1
      FROM manufacturer_active_substances mas1
      WHERE mas1.manufacturer_id = s.supplier_id
        AND mas1.substance_id = :substance_id
    )
  )
ORDER BY s.supplier_name
LIMIT :top OFFSET :skip;
```

## Azure AI Search Knowledge Source configuration

For each MCP tool in the `tools` array:

- `name`: exact tool name
- `inclusionMode`: `reranked`
- `maxOutputTokens`: start with `1000`
- `outputParsing`: `json`
- `jsonParameters.documentsPath`: `$.results[*]`
- `jsonParameters.includeContext`: `false`

Reason:
- Structured JSON output gives predictable, rankable documents.
- Reranking is useful across multiple tool calls.

## Infrastructure plan (Azure PostgreSQL)

Use Azure-Samples/rag-postgres-openai-python as the canonical reference for PostgreSQL Azure infrastructure and postprovision script wiring.

Reference baseline artifacts:

- azure.yaml postprovision sequence: setup_postgres_database, setup_postgres_azurerole, setup_postgres_seeddata
- infra/core/database/postgresql/flexibleserver.bicep
- scripts/setup_postgres_database.sh and scripts/setup_postgres_database.ps1
- scripts/setup_postgres_azurerole.sh and scripts/setup_postgres_azurerole.ps1
- scripts/setup_postgres_seeddata.sh and scripts/setup_postgres_seeddata.ps1

## Bicep additions

1. Add PostgreSQL Flexible Server module under `infra/core/database/postgresql/`.
2. Call module from `infra/main.bicep` using the same deployment/auth pattern as the Azure-Samples baseline.
3. Output:
- server FQDN
- database name
- admin/auth settings required for postprovision scripts

## Authentication

- Preferred: Entra authentication for Azure deployment.
- Local dev fallback: standard password auth in `.env`.

## Postprovision wiring

Update:

- `infra/hooks/postprovision.sh`
- `infra/hooks/postprovision.ps1`

Add steps:

1. Create schema/tables.
2. Load ontology + suppliers JSON.
3. Verify row counts and FK integrity.

## Loader plan

Create one idempotent loader script:

- Input: local `sample-data/json/*.json` and `sample-data/provenance.json`
- Operation: transaction-based truncate-and-reload for v1 simplicity
- Validation:
  - all expected files exist
  - FK checks pass
  - manufacturer IDs exist in suppliers
- Persist provenance into `dataset_provenance`

## Phased delivery

## Phase 1: local data + schema

- Create schema SQL and loader script.
- Validate with local Postgres.

Exit criteria:
- ontology + suppliers loaded successfully
- row counts match source files
- key joins return expected records

## Phase 2: MCP server

- Implement 4 tools and shared response shape.
- Add smoke tests for each tool.

Exit criteria:
- each tool returns deterministic `results/total_count/next_skip`
- pagination and filters validated

## Phase 3: Azure infra + KB integration

- Add PostgreSQL infra to Bicep and azd flow.
- Configure MCP knowledge source with 4 tools.
- Validate retrieve responses and references.

Exit criteria:
- `azd up` provisions DB and loads data
- knowledge base calls tools successfully
- citations/reference quality is acceptable

## Risks and mitigations

1. Too many or overly specific tools reduce tool-selection quality.
- Mitigation: exactly four generic `search_*` tools in v1.

2. Large payloads reduce relevance and increase latency.
- Mitigation: concise `content`, strict `top` limit, compact metadata.

3. Manufacturer context missing if suppliers are not loaded.
- Mitigation: keep suppliers in v1 scope.

4. External MCP latency.
- Mitigation: set `maxRuntimeInSeconds` appropriately on retrieve requests.

## Review checklist

- Scope limited to ontology + suppliers only.
- Exactly 4 tools exposed.
- Output schema standardized across tools.
- No read/write SQL tool in KB v1.
- Azure infra and postprovision hooks include DB create + load.
- Provenance captured for reproducibility.
