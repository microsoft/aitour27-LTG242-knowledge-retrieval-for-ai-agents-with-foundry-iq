"""Smoke-test the deployed PostgreSQL MCP server and its four search tools."""

import asyncio
import os
from typing import Any

from dotenv_azd import load_azd_env
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

EXPECTED_TOOLS = {
    "search_authorizations",
    "search_manufacturers",
    "search_products",
    "search_substances",
}


def require_env(name: str) -> str:
    """Return a required environment variable."""
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


async def test_server(server_url: str, api_key: str) -> None:
    """Verify the tool contract and invoke every PostgreSQL search tool."""
    transport = StreamableHttpTransport(
        server_url,
        headers={"X-MCP-API-Key": api_key},
    )
    async with Client(transport) as client:
        tools = await client.list_tools()
        tool_names = {tool.name for tool in tools}
        if tool_names != EXPECTED_TOOLS:
            missing = sorted(EXPECTED_TOOLS - tool_names)
            unexpected = sorted(tool_names - EXPECTED_TOOLS)
            raise RuntimeError(
                f"MCP tool contract mismatch; missing={missing}, unexpected={unexpected}"
            )

        for tool_name in sorted(EXPECTED_TOOLS):
            result = await client.call_tool(tool_name, {"top": 1})
            data: Any = result.data
            if not isinstance(data, dict) or not data.get("results"):
                raise RuntimeError(f"{tool_name} returned no results")
            print(f"PASS {tool_name}")

        substance_result = await client.call_tool(
            "search_substances",
            {"query": "SUB-001"},
        )
        substance_data: Any = substance_result.data
        products = substance_data["results"][0]["metadata"].get("products", [])
        if not any(product.get("product_id") == "CALD-201" for product in products):
            raise RuntimeError("search_substances did not resolve SUB-001 to CALD-201")
        print("PASS search_substances product relationship")

        manufacturer_result = await client.call_tool(
            "search_manufacturers",
            {"query": "Meridian API Works"},
        )
        manufacturer_data: Any = manufacturer_result.data
        substances = manufacturer_data["results"][0]["metadata"].get("substances", [])
        caldovexine = next(
            (
                substance
                for substance in substances
                if substance.get("substance_id") == "SUB-001"
            ),
            None,
        )
        if not caldovexine or not any(
            product.get("product_id") == "CALD-201"
            for product in caldovexine.get("products", [])
        ):
            raise RuntimeError("Meridian profile did not include SUB-001 to CALD-201")
        print("PASS search_manufacturers product relationship")


def main() -> None:
    """Load deployment settings and run the MCP smoke test."""
    load_azd_env()
    server_url = require_env("POSTGRES_MCP_URL")
    api_key = require_env("MCP_API_KEY")
    asyncio.run(test_server(server_url, api_key))
    print("PostgreSQL MCP smoke test passed.")


if __name__ == "__main__":
    main()