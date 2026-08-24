# PostgreSQL MCP server

This FastMCP service exposes four read-only search tools over the medicinal-product ontology and supplier data:

- `search_products`
- `search_substances`
- `search_authorizations`
- `search_manufacturers`

`azd up` deploys the service to Azure Container Apps and publishes its streamable HTTP endpoint as `POSTGRES_MCP_URL`. The Azure AI Search knowledge base registers that endpoint as the `postgres-ontology-suppliers` MCP knowledge source.

The endpoint requires an `X-MCP-API-Key` header. Generate the key once per azd environment before deploying:

```bash
azd env set MCP_API_KEY "$(openssl rand -hex 32)"
azd up
```

The ignored azd environment stores the value locally. Bicep installs it as a Container App secret, and the Azure AI Search knowledge source stores the matching request header. Run the same commands with a newly generated value to rotate the key.

In Azure, the service uses its user-assigned managed identity to obtain short-lived PostgreSQL access tokens. For local PostgreSQL, set `POSTGRES_PASSWORD` instead.

## Local run

Set `POSTGRES_HOST`, `POSTGRES_DATABASE`, `POSTGRES_USERNAME`, `MCP_API_KEY`, and either the Azure tenant or local password variables, then run:

```bash
uv run --with-requirements requirements.txt python main.py
```

The MCP endpoint is available at `http://localhost:8010/mcp` and requires the same `X-MCP-API-Key` request header.
