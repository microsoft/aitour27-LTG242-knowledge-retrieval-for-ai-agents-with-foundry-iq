"""Create PostgreSQL schema for ontology + suppliers MCP tools."""

import asyncio
import logging
import os

from azure.identity import AzureDeveloperCliCredential
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

logger = logging.getLogger("ltg242.postgres.setup")

TABLE_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS medicinal_products (
        product_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        dosage_form TEXT,
        strength TEXT,
        route_of_administration TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS active_substances (
        substance_id TEXT PRIMARY KEY,
        preferred_name TEXT NOT NULL,
        substance_type TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS regulatory_agencies (
        agency_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        abbreviation TEXT,
        country_or_region TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS marketing_authorizations (
        authorization_id TEXT PRIMARY KEY,
        authorization_number TEXT NOT NULL,
        product_id TEXT NOT NULL REFERENCES medicinal_products(product_id),
        agency_id TEXT NOT NULL REFERENCES regulatory_agencies(agency_id),
        market TEXT,
        status TEXT,
        effective_date DATE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS product_active_substances (
        product_id TEXT NOT NULL REFERENCES medicinal_products(product_id),
        substance_id TEXT NOT NULL REFERENCES active_substances(substance_id),
        PRIMARY KEY (product_id, substance_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS suppliers (
        supplier_id TEXT PRIMARY KEY,
        supplier_name TEXT NOT NULL,
        service_category TEXT NOT NULL,
        address_lines JSONB NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS manufacturer_active_substances (
        manufacturer_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
        substance_id TEXT NOT NULL REFERENCES active_substances(substance_id),
        PRIMARY KEY (manufacturer_id, substance_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS dataset_provenance (
        id SMALLINT PRIMARY KEY DEFAULT 1,
        upstream_repository TEXT NOT NULL,
        upstream_commit TEXT NOT NULL,
        loaded_at_utc TIMESTAMPTZ NOT NULL,
        json_files INT NOT NULL
    )
    """,
]

INDEX_STATEMENTS = [
    "CREATE INDEX IF NOT EXISTS ix_products_name ON medicinal_products(name)",
    "CREATE INDEX IF NOT EXISTS ix_substances_name ON active_substances(preferred_name)",
    (
        "CREATE INDEX IF NOT EXISTS ix_auth_product_status "
        "ON marketing_authorizations(product_id, status)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS ix_auth_agency_status "
        "ON marketing_authorizations(agency_id, status)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS ix_suppliers_category_name "
        "ON suppliers(service_category, supplier_name)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS ix_mfg_substance_manufacturer "
        "ON manufacturer_active_substances(substance_id, manufacturer_id)"
    ),
]

TRGM_STATEMENTS = [
    "CREATE EXTENSION IF NOT EXISTS pg_trgm",
    (
        "CREATE INDEX IF NOT EXISTS ix_products_name_trgm "
        "ON medicinal_products USING gin (name gin_trgm_ops)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS ix_substances_name_trgm "
        "ON active_substances USING gin (preferred_name gin_trgm_ops)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS ix_suppliers_name_trgm "
        "ON suppliers USING gin (supplier_name gin_trgm_ops)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS ix_auth_number_trgm "
        "ON marketing_authorizations USING gin (authorization_number gin_trgm_ops)"
    ),
]


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _build_engine() -> AsyncEngine:
    host = _require_env("POSTGRES_HOST")
    username = _require_env("POSTGRES_USERNAME")
    database = _require_env("POSTGRES_DATABASE")
    sslmode = os.getenv("POSTGRES_SSL", "")

    if host.endswith(".database.azure.com"):
        credential = AzureDeveloperCliCredential(
            tenant_id=_require_env("AZURE_TENANT_ID"),
            process_timeout=60,
        )
        token = credential.get_token("https://ossrdbms-aad.database.windows.net/.default")
        password = token.token
    else:
        password = _require_env("POSTGRES_PASSWORD")

    uri = f"postgresql+asyncpg://{username}:{password}@{host}/{database}"
    if sslmode:
        uri += f"?ssl={sslmode}"
    return create_async_engine(uri, echo=False)


async def main() -> None:
    load_dotenv(override=True)
    engine = _build_engine()
    try:
        async with engine.begin() as conn:
            for stmt in TABLE_STATEMENTS:
                await conn.execute(text(stmt))
            for stmt in INDEX_STATEMENTS:
                await conn.execute(text(stmt))
            try:
                async with conn.begin_nested():
                    for stmt in TRGM_STATEMENTS:
                        await conn.execute(text(stmt))
            except Exception as ex:  # best effort only
                logger.warning("Skipping pg_trgm setup: %s", ex)
    finally:
        await engine.dispose()

    logger.info("PostgreSQL schema setup complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
