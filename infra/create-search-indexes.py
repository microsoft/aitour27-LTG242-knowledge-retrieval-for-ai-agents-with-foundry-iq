"""Create the Stage 1 Azure AI Search index and Foundry IQ knowledge base."""

import asyncio
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote

from azure.core.rest import HttpRequest
from azure.identity.aio import AzureDeveloperCliCredential
from azure.search.documents.indexes.aio import SearchIndexClient, SearchIndexerClient
from azure.search.documents.indexes.models import (
    AzureOpenAIVectorizerParameters,
    KnowledgeBase,
    KnowledgeBaseAzureOpenAIModel,
    KnowledgeSourceReference,
    SearchIndex,
    SearchIndexFieldReference,
    SearchIndexKnowledgeSource,
    SearchIndexKnowledgeSourceParameters,
)
from azure.search.documents.knowledgebases.models import (
    KnowledgeRetrievalLowReasoningEffort,
    KnowledgeRetrievalOutputMode,
)
from azure.storage.blob.aio import BlobServiceClient
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env", override=True)

REPO_ROOT = Path(__file__).parents[1]
DATA_ROOT = REPO_ROOT / "data"
KB1_PDF_GLOB = "**/pdf/*.pdf"
SEARCH_API_VERSION = "2026-05-01-preview"
CONTAINER_NAME = "knowledge"
KB1_BLOB_PREFIX = "kb1"
SEARCH_INDEX_NAME = "session-documents"
KNOWLEDGE_BASE_NAME = "knowledge-retrieval-kb"
EMBEDDING_DIMENSIONS = 3072
SEMANTIC_CONFIGURATION_NAME = "semantic-configuration"
VECTOR_PROFILE_NAME = "vector-search-profile"


def find_kb1_pdfs() -> list[Path]:
    """Return the generated Stage 1 PDFs in a stable upload order."""
    pdfs = sorted(DATA_ROOT.glob(KB1_PDF_GLOB))
    if not pdfs:
        raise FileNotFoundError(f"No Stage 1 PDFs match {DATA_ROOT / KB1_PDF_GLOB}.")
    return pdfs


def build_index(
    index_name: str,
    openai_endpoint: str,
    embedding_deployment: str,
    embedding_model: str,
) -> SearchIndex:
    """Build the chunk index used by the Content Understanding projection."""
    return SearchIndex(
        {
            "name": index_name,
            "fields": [
                {
                    "name": "chunk_id",
                    "type": "Edm.String",
                    "key": True,
                    "searchable": True,
                    "retrievable": True,
                    "stored": True,
                    "sortable": True,
                    "analyzer": "keyword",
                },
                {
                    "name": "parent_id",
                    "type": "Edm.String",
                    "filterable": True,
                    "retrievable": True,
                    "stored": True,
                },
                {
                    "name": "title",
                    "type": "Edm.String",
                    "searchable": True,
                    "retrievable": True,
                    "stored": True,
                },
                {
                    "name": "blob_path",
                    "type": "Edm.String",
                    "filterable": True,
                    "retrievable": True,
                    "stored": True,
                },
                {
                    "name": "chunk",
                    "type": "Edm.String",
                    "searchable": True,
                    "retrievable": True,
                    "stored": True,
                },
                {
                    "name": "page_number_from",
                    "type": "Edm.Int32",
                    "filterable": True,
                    "retrievable": True,
                    "stored": True,
                    "sortable": True,
                },
                {
                    "name": "page_number_to",
                    "type": "Edm.Int32",
                    "filterable": True,
                    "retrievable": True,
                    "stored": True,
                    "sortable": True,
                },
                {
                    "name": "image_path",
                    "type": "Edm.String",
                    "retrievable": True,
                    "stored": True,
                },
                {
                    "name": "text_vector",
                    "type": "Collection(Edm.Single)",
                    "searchable": True,
                    "retrievable": False,
                    "stored": False,
                    "dimensions": EMBEDDING_DIMENSIONS,
                    "vectorSearchProfile": VECTOR_PROFILE_NAME,
                },
            ],
            "semantic": {
                "defaultConfiguration": SEMANTIC_CONFIGURATION_NAME,
                "configurations": [
                    {
                        "name": SEMANTIC_CONFIGURATION_NAME,
                        "prioritizedFields": {
                            "titleField": {"fieldName": "title"},
                            "prioritizedContentFields": [{"fieldName": "chunk"}],
                        },
                    }
                ],
            },
            "vectorSearch": {
                "profiles": [
                    {
                        "name": VECTOR_PROFILE_NAME,
                        "algorithm": "vector-search-algorithm",
                        "vectorizer": "azure-openai-vectorizer",
                    }
                ],
                "algorithms": [
                    {
                        "name": "vector-search-algorithm",
                        "kind": "hnsw",
                        "hnswParameters": {"metric": "cosine"},
                    }
                ],
                "vectorizers": [
                    {
                        "name": "azure-openai-vectorizer",
                        "kind": "azureOpenAI",
                        "azureOpenAIParameters": {
                            "resourceUri": openai_endpoint,
                            "deploymentId": embedding_deployment,
                            "modelName": embedding_model,
                        },
                    }
                ],
            },
        }
    )


def build_indexer_payloads(
    *,
    index_name: str,
    storage_resource_id: str,
    foundry_endpoint: str,
    openai_endpoint: str,
    chat_model: str,
    chat_deployment: str,
    embedding_model: str,
    embedding_deployment: str,
) -> dict[str, tuple[str, dict[str, Any]]]:
    """Build the preview REST resources for the Stage 1 indexer pipeline."""
    data_source_name = f"{index_name}-blob-source"
    skillset_name = f"{index_name}-content-understanding"
    indexer_name = f"{index_name}-blob-indexer"

    data_source = {
        "name": data_source_name,
        "type": "azureblob",
        "credentials": {"connectionString": f"ResourceId={storage_resource_id};"},
        "container": {"name": CONTAINER_NAME, "query": KB1_BLOB_PREFIX},
    }
    skillset = {
        "name": skillset_name,
        "description": "Semantic PDF chunking, image descriptions, and vectorization for KB 1.",
        "skills": [
            {
                "@odata.type": "#Microsoft.Skills.Util.ContentUnderstandingSkill",
                "name": "content-understanding",
                "context": "/document",
                "modelName": chat_model,
                "modelDeployment": chat_deployment,
                "chunkingProperties": {
                    "method": "semantic",
                    "unit": "tokens",
                    "maximumLength": 500,
                },
                "extractionOptions": ["images", "locationMetadata"],
                "inputs": [{"name": "file_data", "source": "/document/file_data"}],
                "outputs": [
                    {"name": "text_sections", "targetName": "text_sections"},
                    {"name": "normalized_images", "targetName": "normalized_images"},
                ],
            },
            {
                "@odata.type": "#Microsoft.Skills.Text.AzureOpenAIEmbeddingSkill",
                "name": "azure-openai-embedding",
                "context": "/document/text_sections/*",
                "resourceUri": openai_endpoint,
                "deploymentId": embedding_deployment,
                "modelName": embedding_model,
                "dimensions": EMBEDDING_DIMENSIONS,
                "inputs": [
                    {"name": "text", "source": "/document/text_sections/*/content"}
                ],
                "outputs": [{"name": "embedding", "targetName": "text_vector"}],
            },
        ],
        "cognitiveServices": {
            "@odata.type": "#Microsoft.Azure.Search.AIServicesByIdentity",
            "subdomainUrl": foundry_endpoint,
            "identity": None,
        },
        "indexProjections": {
            "selectors": [
                {
                    "targetIndexName": index_name,
                    "parentKeyFieldName": "parent_id",
                    "sourceContext": "/document/text_sections/*",
                    "mappings": [
                        {"name": "chunk", "source": "/document/text_sections/*/content"},
                        {
                            "name": "text_vector",
                            "source": "/document/text_sections/*/text_vector",
                        },
                        {
                            "name": "page_number_from",
                            "source": (
                                "/document/text_sections/*/locationMetadata/pageNumberFrom"
                            ),
                        },
                        {
                            "name": "page_number_to",
                            "source": "/document/text_sections/*/locationMetadata/pageNumberTo",
                        },
                        {
                            "name": "image_path",
                            "source": "/document/text_sections/*/imagePath",
                        },
                        {"name": "title", "source": "/document/metadata_storage_name"},
                        {"name": "blob_path", "source": "/document/metadata_storage_path"},
                    ],
                }
            ],
            "parameters": {"projectionMode": "skipIndexingParentDocuments"},
        },
    }
    indexer = {
        "name": indexer_name,
        "dataSourceName": data_source_name,
        "targetIndexName": index_name,
        "skillsetName": skillset_name,
        "parameters": {
            "batchSize": 1,
            "configuration": {
                "dataToExtract": "contentAndMetadata",
                "parsingMode": "default",
                "allowSkillsetToReadFileData": True,
                "indexedFileNameExtensions": ".pdf",
            },
        },
        "fieldMappings": [],
        "outputFieldMappings": [],
    }
    return {
        "datasources": (data_source_name, data_source),
        "skillsets": (skillset_name, skillset),
        "indexers": (indexer_name, indexer),
    }


async def upload_kb1_pdfs(
    storage_account_name: str,
    credential: Any,
    pdfs: list[Path],
) -> int:
    """Upload Stage 1 PDFs to the folder scoped to the KB 1 blob indexer."""
    account_url = f"https://{storage_account_name}.blob.core.windows.net"
    async with BlobServiceClient(account_url=account_url, credential=credential) as service:
        container = service.get_container_client(CONTAINER_NAME)
        for pdf_path in pdfs:
            relative_path = pdf_path.relative_to(DATA_ROOT).as_posix()
            blob = container.get_blob_client(f"{KB1_BLOB_PREFIX}/{relative_path}")
            with pdf_path.open("rb") as pdf_file:
                await blob.upload_blob(pdf_file, overwrite=True)
    return len(pdfs)


async def put_preview_resource(
    client: SearchIndexerClient,
    endpoint: str,
    collection: str,
    name: str,
    payload: dict[str, Any],
) -> None:
    """Create or update a Search resource through the authenticated preview REST API."""
    resource_url = (
        f"{endpoint.rstrip('/')}/{collection}/{quote(name, safe='')}"
        f"?api-version={SEARCH_API_VERSION}"
    )
    response = await client.send_request(
        HttpRequest("PUT", resource_url, headers={"Content-Type": "application/json"}, json=payload)
    )
    response.raise_for_status()


async def create_knowledge_base(
    client: SearchIndexClient,
    *,
    index_name: str,
    knowledge_base_name: str,
    openai_endpoint: str,
    model_deployment: str,
    model_name: str,
) -> None:
    """Create the Search-index knowledge source and Foundry IQ knowledge base."""
    source = SearchIndexKnowledgeSource(
        name=index_name,
        description=(
            "Caldova supplier invoices, cold-chain temperature logs and excursion reports, "
            "and operational quality records covering deviations, nonconformances, "
            "investigations, utility events, and production yield."
        ),
        search_index_parameters=SearchIndexKnowledgeSourceParameters(
            search_index_name=index_name,
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
    await client.create_or_update_knowledge_source(knowledge_source=source)
    knowledge_base = KnowledgeBase(
        name=knowledge_base_name,
        description="Invoice evidence knowledge base for the LTG242 hosted agent.",
        models=[
            KnowledgeBaseAzureOpenAIModel(
                azure_open_ai_parameters=AzureOpenAIVectorizerParameters(
                    resource_url=openai_endpoint,
                    deployment_name=model_deployment,
                    model_name=model_name,
                )
            )
        ],
        knowledge_sources=[KnowledgeSourceReference(name=source.name)],
        retrieval_reasoning_effort=KnowledgeRetrievalLowReasoningEffort(),
        output_mode=KnowledgeRetrievalOutputMode.EXTRACTIVE_DATA,
    )
    await client.create_or_update_knowledge_base(knowledge_base=knowledge_base)


async def main_async() -> None:
    """Upload KB 1 PDFs and configure its indexer-backed knowledge base."""
    endpoint = os.environ["AZURE_AI_SEARCH_SERVICE_ENDPOINT"]
    openai_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
    model_deployment = os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]
    model_name = os.environ["AZURE_OPENAI_CHATGPT_MODEL_NAME"]
    embedding_deployment = os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"]
    embedding_model = os.environ["AZURE_OPENAI_EMBEDDING_MODEL_NAME"]
    storage_account_name = os.environ["AZURE_STORAGE_ACCOUNT_NAME"]
    ai_account_name = os.environ["AZURE_AI_ACCOUNT_NAME"]
    subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
    resource_group = os.environ["AZURE_RESOURCE_GROUP"]
    storage_resource_id = (
        f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}"
        f"/providers/Microsoft.Storage/storageAccounts/{storage_account_name}"
    )
    foundry_endpoint = f"https://{ai_account_name}.services.ai.azure.com"
    pdfs = find_kb1_pdfs()
    credential = AzureDeveloperCliCredential(tenant_id=os.environ["AZURE_TENANT_ID"])

    try:
        uploaded = await upload_kb1_pdfs(storage_account_name, credential, pdfs)
        index = build_index(
            SEARCH_INDEX_NAME,
            openai_endpoint,
            embedding_deployment,
            embedding_model,
        )
        async with SearchIndexClient(endpoint=endpoint, credential=credential) as index_client:
            await index_client.create_or_update_index(index)
            await create_knowledge_base(
                index_client,
                index_name=SEARCH_INDEX_NAME,
                knowledge_base_name=KNOWLEDGE_BASE_NAME,
                openai_endpoint=openai_endpoint,
                model_deployment=model_deployment,
                model_name=model_name,
            )

        pipeline = build_indexer_payloads(
            index_name=SEARCH_INDEX_NAME,
            storage_resource_id=storage_resource_id,
            foundry_endpoint=foundry_endpoint,
            openai_endpoint=openai_endpoint,
            chat_model=model_name,
            chat_deployment=model_deployment,
            embedding_model=embedding_model,
            embedding_deployment=embedding_deployment,
        )
        async with SearchIndexerClient(endpoint=endpoint, credential=credential) as indexer_client:
            for collection, (name, payload) in pipeline.items():
                await put_preview_resource(indexer_client, endpoint, collection, name, payload)
            await indexer_client.run_indexer(pipeline["indexers"][0])

        print(
            f"Uploaded {uploaded} PDFs and started '{pipeline['indexers'][0]}' "
            f"for knowledge base '{KNOWLEDGE_BASE_NAME}'."
        )
    finally:
        await credential.close()


if __name__ == "__main__":
    asyncio.run(main_async())
