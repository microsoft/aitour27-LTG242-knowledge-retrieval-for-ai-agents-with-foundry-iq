"""Create or update a Foundry toolbox backed by a Search knowledge base."""

import os

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    CodeInterpreterToolboxTool,
    MCPToolboxTool,
    ToolboxTool,
)
from azure.identity import AzureDeveloperCliCredential
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env", override=True)

TOOLBOX_CONFIGS = (
    {
        "name_env": "CUSTOM_FOUNDRY_AGENT_TOOLBOX_NAME",
        "name": "knowledge-retrieval-tools",
        "knowledge_base": "knowledge-retrieval-kb",
        "connection_env": "AZURE_AI_SEARCH_KB_MCP_CONNECTION_NAME",
        "connection": "knowledge-base-mcp-connection",
        "description": "Invoice evidence retrieval and code interpreter tools.",
    },
    {
        "name_env": "CUSTOM_SUPPLIER_INTELLIGENCE_TOOLBOX_NAME",
        "name": "supplier-intelligence-tools",
        "knowledge_base": "supplier-intelligence-kb",
        "connection_env": "AZURE_AI_SEARCH_SUPPLIER_KB_MCP_CONNECTION_NAME",
        "connection": "supplier-intelligence-kb-mcp-connection",
        "description": "Supplier intelligence retrieval and code interpreter tools.",
    },
)


def main() -> None:
    """Create scenario-specific toolbox versions and promote them as defaults."""
    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    search_endpoint = os.environ["AZURE_AI_SEARCH_SERVICE_ENDPOINT"]
    credential = AzureDeveloperCliCredential(tenant_id=os.environ["AZURE_TENANT_ID"])
    project = AIProjectClient(endpoint=endpoint, credential=credential)
    for config in TOOLBOX_CONFIGS:
        toolbox_name = os.environ.get(config["name_env"], config["name"])
        connection_name = os.environ.get(
            config["connection_env"], config["connection"]
        )
        knowledge_base_mcp_url = (
            f"{search_endpoint.rstrip('/')}/knowledgebases/"
            f"{config['knowledge_base']}/mcp?api-version=2026-05-01-preview"
        )
        tools: list[ToolboxTool] = [
            CodeInterpreterToolboxTool(
                name="code_interpreter",
                description=(
                    "Run Python for grounded calculations and requested charts or visual "
                    "artifacts."
                ),
            ),
            MCPToolboxTool(
                server_label="knowledge-base",
                server_url=knowledge_base_mcp_url,
                server_description="Retrieve grounded information from the scenario KB.",
                project_connection_id=connection_name,
                allowed_tools=["knowledge_base_retrieve"],
                require_approval="never",
            ),
        ]
        version = project.toolboxes.create_version(
            name=toolbox_name,
            tools=tools,
            description=config["description"],
        )
        project.toolboxes.update(name=toolbox_name, default_version=version.version)
        print(f"Set toolbox '{toolbox_name}' default version to {version.version}.")


if __name__ == "__main__":
    main()
