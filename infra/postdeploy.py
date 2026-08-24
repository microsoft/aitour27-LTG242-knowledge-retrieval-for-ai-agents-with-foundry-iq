"""Grant Azure AI Search access to the deployed hosted-agent identity."""

import json
import os
import subprocess
import uuid

from azure.core.exceptions import HttpResponseError
from azure.identity import AzureDeveloperCliCredential
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.authorization.models import RoleAssignmentCreateParameters
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    KnowledgeBase,
    KnowledgeSourceReference,
    McpServerHeaders,
    McpServerJsonOutputParsing,
    McpServerKnowledgeSource,
    McpServerKnowledgeSourceParameters,
    McpServerOutputParsingJsonParameters,
    McpServerStoredHeadersAuthentication,
    McpServerStoredHeadersParameters,
    McpServerTool,
    SearchIndexFieldReference,
    SearchIndexKnowledgeSource,
    SearchIndexKnowledgeSourceParameters,
)
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env", override=True)

AGENT_NAMES = ("invoice-investigation-agent", "supplier-intelligence-agent")
SEARCH_DATA_CONTRIBUTOR_ROLE_ID = "8ebe5a00-799e-43f5-93ac-243d3dce84a7"
INVOICE_KNOWLEDGE_BASE_NAME = "knowledge-retrieval-kb"
SUPPLIER_KNOWLEDGE_BASE_NAME = "supplier-intelligence-kb"
POSTGRES_MCP_KNOWLEDGE_SOURCE_NAME = "postgres-ontology-suppliers"
SUPPLIER_INDEX_KNOWLEDGE_SOURCE_NAME = "supplier-session-documents"
SESSION_DOCUMENTS_INDEX_NAME = "session-documents"
SEMANTIC_CONFIGURATION_NAME = "semantic-configuration"


def register_postgres_mcp_knowledge_source(
    credential: AzureDeveloperCliCredential,
) -> None:
    """Register the deployed MCP endpoint and attach it to the knowledge base."""
    tools = [
        McpServerTool(
            name=tool_name,
            inclusion_mode="always",
            max_output_tokens=1000,
            output_parsing=McpServerJsonOutputParsing(
                json_parameters=McpServerOutputParsingJsonParameters(
                    documents_path="$.results[*]",
                    include_context=False,
                )
            ),
        )
        for tool_name in (
            "search_products",
            "search_substances",
            "search_authorizations",
            "search_manufacturers",
        )
    ]
    source = McpServerKnowledgeSource(
        name=POSTGRES_MCP_KNOWLEDGE_SOURCE_NAME,
        description=(
            "Caldova suppliers database containing current medicinal products, active "
            "substances, substance-to-product "
            "relationships, marketing authorizations, and supplier-backed "
            "manufacturers. Use substance lookup to resolve an "
            "active substance name or ID to its related Caldova products."
        ),
        mcp_server_parameters=McpServerKnowledgeSourceParameters(
            server_url=os.environ["POSTGRES_MCP_URL"],
            authentication=McpServerStoredHeadersAuthentication(
                stored_headers_parameters=McpServerStoredHeadersParameters(
                    headers=McpServerHeaders(
                        {"X-MCP-API-Key": os.environ["MCP_API_KEY"]}
                    )
                )
            ),
            tools=tools,
        ),
    )
    indexed_source = SearchIndexKnowledgeSource(
        name=SUPPLIER_INDEX_KNOWLEDGE_SOURCE_NAME,
        description=(
            "Caldova supplier invoices, cold-chain records, and operational quality "
            "evidence from the session documents index."
        ),
        search_index_parameters=SearchIndexKnowledgeSourceParameters(
            search_index_name=SESSION_DOCUMENTS_INDEX_NAME,
            source_data_fields=[
                SearchIndexFieldReference(name=field_name)
                for field_name in (
                    "chunk_id",
                    "parent_id",
                    "title",
                    "blob_path",
                    "chunk",
                    "page_number_from",
                    "page_number_to",
                    "image_path",
                )
            ],
            search_fields=[SearchIndexFieldReference(name="chunk")],
            semantic_configuration_name=SEMANTIC_CONFIGURATION_NAME,
        ),
    )

    client = SearchIndexClient(
        endpoint=os.environ["AZURE_AI_SEARCH_SERVICE_ENDPOINT"],
        credential=credential,
    )
    client.create_or_update_knowledge_source(source)
    client.create_or_update_knowledge_source(indexed_source)
    invoice_knowledge_base = client.get_knowledge_base(INVOICE_KNOWLEDGE_BASE_NAME)
    supplier_knowledge_base = KnowledgeBase(
        name=SUPPLIER_KNOWLEDGE_BASE_NAME,
        description=(
            "Supplier intelligence combining indexed evidence with current facts from the "
            "Caldova suppliers database. "
            "For cross-source questions, use canonical identifiers or names from documents "
            "to retrieve related database records, and use explicit database relationships "
            "for entity mappings rather than inferring relationships from document "
            "co-occurrence."
        ),
        models=invoice_knowledge_base.models,
        knowledge_sources=[
            KnowledgeSourceReference(name=indexed_source.name),
            KnowledgeSourceReference(name=source.name),
        ],
        retrieval_reasoning_effort=invoice_knowledge_base.retrieval_reasoning_effort,
        output_mode=invoice_knowledge_base.output_mode,
    )
    client.create_or_update_knowledge_base(supplier_knowledge_base)

    invoice_sources = [
        reference
        for reference in invoice_knowledge_base.knowledge_sources
        if reference.name != source.name
    ]
    if len(invoice_sources) != len(invoice_knowledge_base.knowledge_sources):
        invoice_knowledge_base.knowledge_sources = invoice_sources
        client.create_or_update_knowledge_base(invoice_knowledge_base)

    print(
        f"Registered MCP knowledge source '{source.name}' on "
        f"'{SUPPLIER_KNOWLEDGE_BASE_NAME}'."
    )


def get_agent_principal_id(agent_name: str) -> str | None:
    """Return the managed identity principal ID when the hosted agent is deployed."""
    command_env = os.environ.copy()
    command_env["AZURE_DEV_USER_AGENT"] = "microsoft_foundry_skill"
    try:
        result = subprocess.run(
            [
                "azd",
                "ai",
                "agent",
                "show",
                agent_name,
                "--output",
                "json",
                "--no-prompt",
            ],
            check=True,
            capture_output=True,
            text=True,
            env=command_env,
        )
    except subprocess.CalledProcessError:
        print(f"Skipping Search access for undeployed agent {agent_name}.")
        return None
    agent = json.loads(result.stdout)
    principal_id = agent.get("instance_identity", {}).get("principal_id")
    if not principal_id:
        raise RuntimeError(f"Could not retrieve the hosted identity for {agent_name}.")
    return principal_id


def main() -> None:
    """Assign Search Index Data Contributor to each hosted-agent identity."""

    subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
    resource_group = os.environ["AZURE_RESOURCE_GROUP"]
    service_name = os.environ["AZURE_AI_SEARCH_SERVICE_NAME"]
    scope = (
        f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}"
        f"/providers/Microsoft.Search/searchServices/{service_name}"
    )
    role_definition_id = (
        f"{scope}/providers/Microsoft.Authorization/roleDefinitions/"
        f"{SEARCH_DATA_CONTRIBUTOR_ROLE_ID}"
    )
    credential = AzureDeveloperCliCredential(tenant_id=os.environ["AZURE_TENANT_ID"])
    client = AuthorizationManagementClient(credential, subscription_id)
    for agent_name in AGENT_NAMES:
        principal_id = get_agent_principal_id(agent_name)
        if principal_id is None:
            continue
        assignment_name = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"{scope}:{principal_id}:{SEARCH_DATA_CONTRIBUTOR_ROLE_ID}",
            )
        )
        parameters = RoleAssignmentCreateParameters(
            principal_id=principal_id,
            principal_type="ServicePrincipal",
            role_definition_id=role_definition_id,
        )
        try:
            client.role_assignments.create(scope, assignment_name, parameters)
        except HttpResponseError as error:
            if error.status_code != 409:
                raise
            print(f"Search access is already assigned to {agent_name}.")
        else:
            print(f"Assigned Search Index Data Contributor to {agent_name}.")

    register_postgres_mcp_knowledge_source(credential)


if __name__ == "__main__":
    main()
