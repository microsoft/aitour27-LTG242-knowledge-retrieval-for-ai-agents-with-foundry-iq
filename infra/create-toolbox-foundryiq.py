"""Create or update a Foundry toolbox backed by a Search knowledge base."""

import os

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    CodeInterpreterToolboxTool,
    MCPToolboxTool,
    ToolboxTool,
    WebSearchToolboxTool,
)
from azure.identity import AzureDeveloperCliCredential
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env", override=True)


def main() -> None:
    """Create a toolbox version and promote it as the default version."""
    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    search_endpoint = os.environ["AZURE_AI_SEARCH_SERVICE_ENDPOINT"]
    toolbox_name = os.environ.get("CUSTOM_FOUNDRY_AGENT_TOOLBOX_NAME", "knowledge-retrieval-tools")
    knowledge_base_name = os.environ.get(
        "AZURE_AI_SEARCH_KNOWLEDGE_BASE_NAME", "knowledge-retrieval-kb"
    )
    connection_name = os.environ.get(
        "AZURE_AI_SEARCH_KB_MCP_CONNECTION_NAME", "knowledge-base-mcp-connection"
    )
    knowledge_base_mcp_url = (
        f"{search_endpoint.rstrip('/')}/knowledgebases/{knowledge_base_name}"
        "/mcp?api-version=2026-05-01-preview"
    )
    credential = AzureDeveloperCliCredential(tenant_id=os.environ["AZURE_TENANT_ID"])
    tools: list[ToolboxTool] = [
        WebSearchToolboxTool(
            name="web_search",
            description="Search the public web for current information.",
            search_context_size="medium",
        ),
        CodeInterpreterToolboxTool(
            name="code_interpreter",
            description="Run Python for calculations and structured data analysis.",
        ),
        MCPToolboxTool(
            server_label="knowledge-base",
            server_url=knowledge_base_mcp_url,
            server_description="Retrieve grounded information from the session knowledge base.",
            project_connection_id=connection_name,
            allowed_tools=["knowledge_base_retrieve"],
            require_approval="never",
        ),
    ]

    project = AIProjectClient(endpoint=endpoint, credential=credential)
    version = project.toolboxes.create_version(
        name=toolbox_name,
        tools=tools,
        description="Retrieval, web search, and code interpreter tools for the hosted agent.",
    )
    project.toolboxes.update(name=toolbox_name, default_version=version.version)
    print(f"Set toolbox '{toolbox_name}' default version to {version.version}.")


if __name__ == "__main__":
    main()
