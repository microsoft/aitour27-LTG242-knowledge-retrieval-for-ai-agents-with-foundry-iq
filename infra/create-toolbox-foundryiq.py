"""Create or update a Foundry toolbox backed by a Search knowledge base."""

import os

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    CodeInterpreterToolboxTool,
    MCPToolboxTool,
    ToolboxTool,
)
from azure.identity import AzureDeveloperCliCredential
from dotenv_azd import load_azd_env

load_azd_env()

TOOLBOX_CONFIGS = (
    {
        "name": "knowledge-retrieval-tools",
        "knowledge_base": "knowledge-retrieval-kb",
        "connection": "knowledge-base-mcp-connection",
        "description": "Invoice evidence retrieval and code interpreter tools.",
    },
    {
        "name": "supplier-intelligence-tools",
        "knowledge_base": "supplier-intelligence-kb",
        "connection": "supplier-intelligence-kb-mcp-connection",
        "description": "Supplier intelligence retrieval and code interpreter tools.",
    },
    {
        "name": "sourcing-review-tools",
        "knowledge_base": "sourcing-review-kb",
        "connection": "sourcing-review-kb-mcp-connection",
        "description": "Sourcing review with ACL-filtered evidence and code interpreter tools.",
    },
)


def main() -> None:
    """Create scenario-specific toolbox versions and promote them as defaults."""
    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    search_endpoint = os.environ["AZURE_AI_SEARCH_SERVICE_ENDPOINT"]
    credential = AzureDeveloperCliCredential(tenant_id=os.environ["AZURE_TENANT_ID"])
    project = AIProjectClient(endpoint=endpoint, credential=credential)
    for config in TOOLBOX_CONFIGS:
        toolbox_name = config["name"]
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
                project_connection_id=config["connection"],
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
