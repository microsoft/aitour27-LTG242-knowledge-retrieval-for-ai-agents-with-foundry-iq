"""Seed PostgreSQL tables from local sample-data JSON snapshot."""

import asyncio
import json
import logging
import os
from datetime import UTC, date, datetime
from pathlib import Path

from azure.identity import AzureDeveloperCliCredential
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

logger = logging.getLogger("ltg242.postgres.seed")

REPO_ROOT = Path(__file__).parents[1]
JSON_DIR = REPO_ROOT / "sample-data" / "json"
PROVENANCE_PATH = REPO_ROOT / "sample-data" / "provenance.json"


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _load_json(name: str) -> dict:
    path = JSON_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


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

    suppliers_payload = _load_json("suppliers.json")
    ontology_payload = _load_json("medicinal-product-ontology.json")
    provenance = json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))

    engine = _build_engine()
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "TRUNCATE TABLE manufacturer_active_substances, "
                    "product_active_substances, marketing_authorizations, suppliers, "
                    "active_substances, regulatory_agencies, medicinal_products "
                    "RESTART IDENTITY CASCADE"
                )
            )

            for row in ontology_payload["medicinal_products"]:
                await conn.execute(
                    text(
                        """
                        INSERT INTO medicinal_products
                          (product_id, name, dosage_form, strength,
                           route_of_administration)
                        VALUES
                          (:product_id, :name, :dosage_form, :strength,
                           :route_of_administration)
                        """
                    ),
                    row,
                )

            for row in ontology_payload["active_substances"]:
                await conn.execute(
                    text(
                        """
                        INSERT INTO active_substances (substance_id, preferred_name, substance_type)
                        VALUES (:substance_id, :preferred_name, :substance_type)
                        """
                    ),
                    row,
                )

            for row in ontology_payload["regulatory_agencies"]:
                await conn.execute(
                    text(
                        """
                        INSERT INTO regulatory_agencies
                          (agency_id, name, abbreviation, country_or_region)
                        VALUES (:agency_id, :name, :abbreviation, :country_or_region)
                        """
                    ),
                    row,
                )

            for row in ontology_payload["marketing_authorizations"]:
                await conn.execute(
                    text(
                        """
                        INSERT INTO marketing_authorizations
                                  (authorization_id, authorization_number,
                                    product_id, agency_id, market, status,
                                    effective_date)
                        VALUES
                                  (:authorization_id, :authorization_number,
                                    :product_id, :agency_id, :market, :status,
                                    :effective_date)
                        """
                    ),
                    {
                        **row,
                        "effective_date": (
                            date.fromisoformat(row["effective_date"])
                            if row["effective_date"]
                            else None
                        ),
                    },
                )

            for row in suppliers_payload["suppliers"]:
                await conn.execute(
                    text(
                        """
                        INSERT INTO suppliers
                          (supplier_id, supplier_name, service_category,
                           address_lines)
                        VALUES
                          (:supplier_id, :supplier_name, :service_category,
                           CAST(:address_lines AS JSONB))
                        """
                    ),
                    {
                        "supplier_id": row["supplier_id"],
                        "supplier_name": row["supplier_name"],
                        "service_category": row["service_category"],
                        "address_lines": json.dumps(row["address_lines"]),
                    },
                )

            for row in ontology_payload["product_active_substances"]:
                await conn.execute(
                    text(
                        """
                        INSERT INTO product_active_substances (product_id, substance_id)
                        VALUES (:product_id, :substance_id)
                        """
                    ),
                    row,
                )

            for row in ontology_payload["manufacturer_active_substances"]:
                await conn.execute(
                    text(
                        """
                        INSERT INTO manufacturer_active_substances (manufacturer_id, substance_id)
                        VALUES (:manufacturer_id, :substance_id)
                        """
                    ),
                    row,
                )

            await conn.execute(
                text(
                    """
                    INSERT INTO dataset_provenance
                      (id, upstream_repository, upstream_commit, loaded_at_utc,
                       json_files)
                    VALUES (1, :repository, :commit, :loaded_at_utc, :json_files)
                    ON CONFLICT (id) DO UPDATE
                    SET upstream_repository = EXCLUDED.upstream_repository,
                        upstream_commit = EXCLUDED.upstream_commit,
                        loaded_at_utc = EXCLUDED.loaded_at_utc,
                        json_files = EXCLUDED.json_files
                    """
                ),
                {
                    "repository": provenance["repository"],
                    "commit": provenance["commit"],
                    "loaded_at_utc": datetime.now(UTC),
                    "json_files": provenance.get("jsonCount", 0),
                },
            )
    finally:
        await engine.dispose()

    logger.info("PostgreSQL seed load complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
