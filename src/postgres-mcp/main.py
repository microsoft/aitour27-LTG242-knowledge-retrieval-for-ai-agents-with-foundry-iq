"""PostgreSQL-backed MCP server exposing generic search tools."""

from __future__ import annotations

import json
import logging
import os
import secrets
from typing import Any

import psycopg
from azure.identity import AzureDeveloperCliCredential, ManagedIdentityCredential
from dotenv import load_dotenv
from fastmcp import FastMCP
from sqlalchemy import create_engine, text
from starlette.middleware import Middleware
from starlette.responses import PlainTextResponse

logger = logging.getLogger("ltg242.postgres_mcp")
load_dotenv(override=True)


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _build_engine():
    host = _require_env("POSTGRES_HOST")
    username = _require_env("POSTGRES_USERNAME")
    database = _require_env("POSTGRES_DATABASE")
    sslmode = os.getenv("POSTGRES_SSL", "")

    if host.endswith(".database.azure.com"):
        client_id = os.getenv("AZURE_CLIENT_ID")
        credential = (
            ManagedIdentityCredential(client_id=client_id)
            if client_id
            else AzureDeveloperCliCredential(
              tenant_id=_require_env("AZURE_TENANT_ID"),
                process_timeout=60,
            )
        )

        def connect() -> psycopg.Connection:
            token = credential.get_token(
                "https://ossrdbms-aad.database.windows.net/.default"
            )
            return psycopg.connect(
                host=host,
                dbname=database,
                user=username,
                password=token.token,
                sslmode=sslmode or "require",
                connect_timeout=5,
            )
    else:
        password = _require_env("POSTGRES_PASSWORD")

        def connect() -> psycopg.Connection:
            return psycopg.connect(
                host=host,
                dbname=database,
                user=username,
                password=password,
                sslmode=sslmode or "prefer",
                connect_timeout=5,
            )

    return create_engine(
        "postgresql+psycopg://",
        creator=connect,
        pool_pre_ping=True,
        pool_recycle=300,
    )


ENGINE = _build_engine()
MCP_API_KEY = _require_env("MCP_API_KEY")
mcp = FastMCP("ontology-suppliers-search")


class ApiKeyMiddleware:
  def __init__(self, app: Any) -> None:
    self.app = app

  async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
    if scope["type"] == "http":
      headers = dict(scope.get("headers", []))
      provided_key = headers.get(b"x-mcp-api-key", b"").decode("utf-8")
      if not secrets.compare_digest(provided_key, MCP_API_KEY):
        response = PlainTextResponse("Unauthorized", status_code=401)
        await response(scope, receive, send)
        return
    await self.app(scope, receive, send)


def _safe_top(top: int) -> int:
    return max(1, min(top, 50))


def _rows_to_results(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    parsed: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        metadata = item.get("metadata")
        if isinstance(metadata, str):
            try:
                item["metadata"] = json.loads(metadata)
            except json.JSONDecodeError:
                item["metadata"] = {"raw": metadata}
        parsed.append(item)
    return parsed


def _run_query(
    sql: str,
    params: dict[str, Any],
    count_sql: str,
    count_params: dict[str, Any],
    skip: int,
    top: int,
) -> dict[str, Any]:
    with ENGINE.begin() as conn:
        conn.execute(text("SET LOCAL statement_timeout = 5000"))
        result = conn.execute(text(sql), params)
        rows = [dict(row._mapping) for row in result]
        count_result = conn.execute(text(count_sql), count_params)
        total_count = int(count_result.scalar_one())

    next_skip = skip + top if skip + top < total_count else None
    return {
        "results": _rows_to_results(rows),
        "total_count": total_count,
        "next_skip": next_skip,
    }


@mcp.tool(
  description=(
    "Search current medicinal product records by product name, strength, dosage form, "
    "or route of administration. Returns product identifiers and formulation details."
  )
)
def search_products(
    query: str | None = None,
    dosage_form: str | None = None,
    route_of_administration: str | None = None,
    top: int = 10,
    skip: int = 0,
) -> dict[str, Any]:
    top = _safe_top(top)
    skip = max(0, skip)

    sql = """
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
    WHERE (
        CAST(:query AS TEXT) IS NULL OR :query = ''
        OR to_tsvector(
          'simple',
          concat_ws(
            ' ', p.product_id, p.name, p.dosage_form, p.strength,
            p.route_of_administration
          )
        ) @@ plainto_tsquery('simple', :query)
      )
      AND (CAST(:dosage_form AS TEXT) IS NULL OR p.dosage_form = :dosage_form)
      AND (
        CAST(:route_of_administration AS TEXT) IS NULL
        OR p.route_of_administration = :route_of_administration
      )
    ORDER BY p.name
    LIMIT :top OFFSET :skip
    """

    count_sql = """
    SELECT count(*)
    FROM medicinal_products p
    WHERE (
        CAST(:query AS TEXT) IS NULL OR :query = ''
        OR to_tsvector(
          'simple',
          concat_ws(
            ' ', p.product_id, p.name, p.dosage_form, p.strength,
            p.route_of_administration
          )
        ) @@ plainto_tsquery('simple', :query)
      )
      AND (CAST(:dosage_form AS TEXT) IS NULL OR p.dosage_form = :dosage_form)
      AND (
        CAST(:route_of_administration AS TEXT) IS NULL
        OR p.route_of_administration = :route_of_administration
      )
    """

    params = {
        "query": query,
        "dosage_form": dosage_form,
        "route_of_administration": route_of_administration,
        "top": top,
        "skip": skip,
    }
    return _run_query(sql, params, count_sql, params, skip, top)


@mcp.tool(
  description=(
    "Search current active-substance records by preferred name or substance type. "
    "Use this tool to resolve a substance name or ID to related medicinal products; "
    "related products are included by default."
  )
)
def search_substances(
    query: str | None = None,
    substance_type: str | None = None,
    include_products: bool = True,
    top: int = 10,
    skip: int = 0,
) -> dict[str, Any]:
    top = _safe_top(top)
    skip = max(0, skip)

    if include_products:
        sql = """
        SELECT
          s.substance_id AS id,
          s.preferred_name AS title,
          s.substance_type AS content,
          'substance' AS entity_type,
          'postgres/ontology_suppliers' AS source,
          jsonb_build_object(
            'substance_id', s.substance_id,
            'substance_type', s.substance_type,
            'products', (
              SELECT jsonb_agg(
                jsonb_build_object('product_id', p.product_id, 'name', p.name)
                ORDER BY p.name
              )
              FROM product_active_substances pas
              JOIN medicinal_products p ON p.product_id = pas.product_id
              WHERE pas.substance_id = s.substance_id
            )
          ) AS metadata
        FROM active_substances s
        WHERE (
          CAST(:query AS TEXT) IS NULL OR :query = ''
          OR s.substance_id ILIKE '%' || :query || '%'
          OR s.preferred_name ILIKE '%' || :query || '%'
        )
          AND (CAST(:substance_type AS TEXT) IS NULL OR s.substance_type = :substance_type)
        ORDER BY s.preferred_name
        LIMIT :top OFFSET :skip
        """
    else:
        sql = """
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
        WHERE (
          CAST(:query AS TEXT) IS NULL OR :query = ''
          OR s.substance_id ILIKE '%' || :query || '%'
          OR s.preferred_name ILIKE '%' || :query || '%'
        )
          AND (CAST(:substance_type AS TEXT) IS NULL OR s.substance_type = :substance_type)
        ORDER BY s.preferred_name
        LIMIT :top OFFSET :skip
        """

    count_sql = """
    SELECT count(*)
    FROM active_substances s
    WHERE (
      CAST(:query AS TEXT) IS NULL OR :query = ''
      OR s.substance_id ILIKE '%' || :query || '%'
      OR s.preferred_name ILIKE '%' || :query || '%'
    )
      AND (CAST(:substance_type AS TEXT) IS NULL OR s.substance_type = :substance_type)
    """

    params = {
        "query": query,
        "substance_type": substance_type,
        "top": top,
        "skip": skip,
    }
    return _run_query(sql, params, count_sql, params, skip, top)


@mcp.tool(
  description=(
    "Search current marketing authorization records by product, authorization number, "
    "regulatory agency, market, or status."
  )
)
def search_authorizations(
    query: str | None = None,
    product_id: str | None = None,
    agency_id: str | None = None,
    market: str | None = None,
    status: str | None = None,
    top: int = 10,
    skip: int = 0,
) -> dict[str, Any]:
    top = _safe_top(top)
    skip = max(0, skip)

    sql = """
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
        CAST(:query AS TEXT) IS NULL OR :query = ''
        OR a.authorization_number ILIKE '%' || :query || '%'
        OR p.name ILIKE '%' || :query || '%'
        OR r.name ILIKE '%' || :query || '%'
      )
      AND (CAST(:product_id AS TEXT) IS NULL OR a.product_id = :product_id)
      AND (CAST(:agency_id AS TEXT) IS NULL OR a.agency_id = :agency_id)
      AND (CAST(:market AS TEXT) IS NULL OR a.market = :market)
      AND (CAST(:status AS TEXT) IS NULL OR a.status = :status)
    ORDER BY a.authorization_number
    LIMIT :top OFFSET :skip
    """

    count_sql = """
    SELECT count(*)
    FROM marketing_authorizations a
    JOIN medicinal_products p ON p.product_id = a.product_id
    JOIN regulatory_agencies r ON r.agency_id = a.agency_id
    WHERE (
        CAST(:query AS TEXT) IS NULL OR :query = ''
        OR a.authorization_number ILIKE '%' || :query || '%'
        OR p.name ILIKE '%' || :query || '%'
        OR r.name ILIKE '%' || :query || '%'
      )
      AND (CAST(:product_id AS TEXT) IS NULL OR a.product_id = :product_id)
      AND (CAST(:agency_id AS TEXT) IS NULL OR a.agency_id = :agency_id)
      AND (CAST(:market AS TEXT) IS NULL OR a.market = :market)
      AND (CAST(:status AS TEXT) IS NULL OR a.status = :status)
    """

    params = {
        "query": query,
        "product_id": product_id,
        "agency_id": agency_id,
        "market": market,
        "status": status,
        "top": top,
        "skip": skip,
    }
    return _run_query(sql, params, count_sql, params, skip, top)


@mcp.tool(
  description=(
    "Search current manufacturer and supplier records by name, country, or active "
    "substance identifier. Returns each manufacturer's active substances and their "
    "related medicinal products."
  )
)
def search_manufacturers(
    query: str | None = None,
    country: str | None = None,
    substance_id: str | None = None,
    top: int = 10,
    skip: int = 0,
) -> dict[str, Any]:
    top = _safe_top(top)
    skip = max(0, skip)

    sql = """
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
        'substances', (
          SELECT jsonb_agg(
            jsonb_build_object(
              'substance_id', active_substance.substance_id,
              'preferred_name', active_substance.preferred_name,
              'products', (
                SELECT jsonb_agg(
                  jsonb_build_object(
                    'product_id', product.product_id,
                    'name', product.name
                  )
                  ORDER BY product.name
                )
                FROM product_active_substances product_substance
                JOIN medicinal_products product
                  ON product.product_id = product_substance.product_id
                WHERE product_substance.substance_id = active_substance.substance_id
              )
            )
            ORDER BY active_substance.substance_id
          )
          FROM manufacturer_active_substances manufacturer_substance
          JOIN active_substances active_substance
            ON active_substance.substance_id = manufacturer_substance.substance_id
          WHERE manufacturer_substance.manufacturer_id = s.supplier_id
        )
      ) AS metadata
    FROM suppliers s
    WHERE EXISTS (
        SELECT 1
        FROM manufacturer_active_substances mas0
        WHERE mas0.manufacturer_id = s.supplier_id
      )
      AND (
        CAST(:query AS TEXT) IS NULL OR :query = ''
        OR s.supplier_name ILIKE '%' || :query || '%'
      )
      AND (CAST(:country AS TEXT) IS NULL OR s.address_lines->>2 = :country)
      AND (
        CAST(:substance_id AS TEXT) IS NULL
        OR EXISTS (
          SELECT 1
          FROM manufacturer_active_substances mas1
          WHERE mas1.manufacturer_id = s.supplier_id
            AND mas1.substance_id = :substance_id
        )
      )
    ORDER BY s.supplier_name
    LIMIT :top OFFSET :skip
    """

    count_sql = """
    SELECT count(*)
    FROM suppliers s
    WHERE EXISTS (
        SELECT 1
        FROM manufacturer_active_substances mas0
        WHERE mas0.manufacturer_id = s.supplier_id
      )
      AND (
        CAST(:query AS TEXT) IS NULL OR :query = ''
        OR s.supplier_name ILIKE '%' || :query || '%'
      )
      AND (CAST(:country AS TEXT) IS NULL OR s.address_lines->>2 = :country)
      AND (
        CAST(:substance_id AS TEXT) IS NULL
        OR EXISTS (
          SELECT 1
          FROM manufacturer_active_substances mas1
          WHERE mas1.manufacturer_id = s.supplier_id
            AND mas1.substance_id = :substance_id
        )
      )
    """

    params = {
        "query": query,
        "country": country,
        "substance_id": substance_id,
        "top": top,
        "skip": skip,
    }
    return _run_query(sql, params, count_sql, params, skip, top)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8010")),
        stateless_http=True,
        json_response=True,
      middleware=[Middleware(ApiKeyMiddleware)],
    )
