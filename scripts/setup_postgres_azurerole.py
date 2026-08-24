"""Create the read-only PostgreSQL role used by the MCP managed identity."""

import asyncio
import logging
import os

from azure.identity import AzureDeveloperCliCredential
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

logger = logging.getLogger("ltg242.postgres.role")


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _quote_identifier(value: str) -> str:
    return f'"{value.replace(chr(34), chr(34) * 2)}"'


async def main() -> None:
    load_dotenv(override=True)
    host = _require_env("POSTGRES_HOST")
    if not host.endswith(".database.azure.com"):
        logger.info("Skipping Entra role setup for non-Azure PostgreSQL.")
        return

    admin_username = _require_env("POSTGRES_USERNAME")
    database = _require_env("POSTGRES_DATABASE")
    identity_name = _require_env("SERVICE_POSTGRES_MCP_IDENTITY_NAME")
    credential = AzureDeveloperCliCredential(
        tenant_id=os.getenv("AZURE_TENANT_ID"),
        process_timeout=60,
    )
    token = credential.get_token("https://ossrdbms-aad.database.windows.net/.default")
    admin_engine = create_async_engine(
        f"postgresql+asyncpg://{admin_username}:{token.token}@{host}/postgres?ssl=require"
    )
    database_engine = create_async_engine(
        f"postgresql+asyncpg://{admin_username}:{token.token}@{host}/{database}?ssl=require"
    )

    quoted_identity = _quote_identifier(identity_name)
    quoted_database = _quote_identifier(database)
    try:
        async with admin_engine.begin() as conn:
            existing = await conn.execute(
                text(
                    "SELECT 1 FROM pg_catalog.pgaadauth_list_principals(false) "
                    "WHERE rolname = :identity_name"
                ),
                {"identity_name": identity_name},
            )
            if existing.scalar_one_or_none() is None:
                await conn.execute(
                    text(
                        "SELECT * FROM pg_catalog.pgaadauth_create_principal"
                        "(:identity_name, false, false)"
                    ),
                    {"identity_name": identity_name},
                )

            await conn.execute(
                text(f"GRANT CONNECT ON DATABASE {quoted_database} TO {quoted_identity}")
            )

        async with database_engine.begin() as conn:
            await conn.execute(text(f"GRANT USAGE ON SCHEMA public TO {quoted_identity}"))
            await conn.execute(
                text(f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {quoted_identity}")
            )
            await conn.execute(
                text(
                    "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
                    f"GRANT SELECT ON TABLES TO {quoted_identity}"
                )
            )
    finally:
        await admin_engine.dispose()
        await database_engine.dispose()

    logger.info("Configured read-only PostgreSQL role for %s.", identity_name)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
