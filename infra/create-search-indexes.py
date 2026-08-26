"""Create the Search indexes and Foundry IQ knowledge bases."""

import asyncio
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote

from azure.core.exceptions import ResourceNotFoundError
from azure.core.rest import HttpRequest
from azure.identity.aio import AzureDeveloperCliCredential
from azure.search.documents.aio import SearchClient
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
from dotenv_azd import load_azd_env

load_azd_env()

REPO_ROOT = Path(__file__).parents[1]
SAMPLE_DATA_ROOT = REPO_ROOT / "sample-data"
CORPORA_PATH = SAMPLE_DATA_ROOT / "corpora.json"
PROVENANCE_PATH = SAMPLE_DATA_ROOT / "provenance.json"
KB1_CORPUS_NAME = "invoice-investigation"
KB1_EXPECTED_PDF_COUNT = 25
SEARCH_API_VERSION = "2026-05-01-preview"
CONTAINER_NAME = "knowledge"
EXTRACTED_IMAGES_CONTAINER_NAME = "extracted-images"
KB1_BLOB_PREFIX = "kb1"
SEARCH_INDEX_NAME = "session-documents"
KNOWLEDGE_BASE_NAME = "knowledge-retrieval-kb"
EMBEDDING_DIMENSIONS = 3072
SEMANTIC_CONFIGURATION_NAME = "semantic-configuration"
VECTOR_PROFILE_NAME = "vector-search-profile"
INDEXER_POLL_SECONDS = 10

# KB 2 ACL-aware resources
KB2_CONTAINER_NAME = "kb2-sourcing"
KB2_INDEX_NAME = "sourcing-documents"
KB2_KNOWLEDGE_BASE_NAME = "sourcing-review-kb"


def find_kb1_pdfs() -> tuple[list[Path], dict[str, Any]]:
    """Return the manifest-selected Stage 1 PDFs and upstream provenance."""
    try:
        corpora = json.loads(CORPORA_PATH.read_text(encoding="utf-8"))
        provenance = json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))
        relative_paths = corpora[KB1_CORPUS_NAME]
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as error:
        raise RuntimeError(
            "The sample-data snapshot is missing or invalid. "
            "Run 'uv run python scripts/sync_sample_data.py'."
        ) from error

    if not isinstance(relative_paths, list) or not all(
        isinstance(relative_path, str) for relative_path in relative_paths
    ):
        raise RuntimeError(f"Corpus '{KB1_CORPUS_NAME}' must be a list of PDF paths.")
    if len(relative_paths) != len(set(relative_paths)):
        raise RuntimeError(f"Corpus '{KB1_CORPUS_NAME}' contains duplicate paths.")

    pdfs = [SAMPLE_DATA_ROOT / relative_path for relative_path in relative_paths]
    missing = [str(pdf.relative_to(REPO_ROOT)) for pdf in pdfs if not pdf.is_file()]
    if len(pdfs) != KB1_EXPECTED_PDF_COUNT or missing:
        raise RuntimeError(
            f"Expected {KB1_EXPECTED_PDF_COUNT} PDFs in corpus '{KB1_CORPUS_NAME}', "
            f"found {len(pdfs)} with missing files: {missing or 'none'}."
        )
    return pdfs, provenance


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
                    "name": "metadata_storage_path",
                    "type": "Edm.String",
                    "filterable": True,
                    "retrievable": False,
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
                    "maximumLength": 2000,
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
        "knowledgeStore": {
            "storageConnectionString": f"ResourceId={storage_resource_id}/;",
            "projections": [
                {
                    "tables": [],
                    "objects": [],
                    "files": [
                        {
                            "storageContainer": EXTRACTED_IMAGES_CONTAINER_NAME,
                            "source": "/document/normalized_images/*",
                        }
                    ],
                }
            ],
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


def build_kb2_acl_index(
    index_name: str,
    openai_endpoint: str,
    embedding_deployment: str,
    embedding_model: str,
) -> SearchIndex:
    """Build the ACL-aware KB 2 index with permission fields for document-level access control."""
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
                    "name": "metadata_storage_path",
                    "type": "Edm.String",
                    "filterable": True,
                    "retrievable": False,
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
                # Permission fields for ACL enforcement
                {
                    "name": "user_ids",
                    "type": "Collection(Edm.String)",
                    "permissionFilter": "userIds",
                    "filterable": True,
                    "retrievable": False,
                    "stored": True,
                },
                {
                    "name": "group_ids",
                    "type": "Collection(Edm.String)",
                    "permissionFilter": "groupIds",
                    "filterable": True,
                    "retrievable": False,
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
            "permissionFilterOption": "enabled",
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


def build_kb2_indexer_payloads(
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
    """Build the ACL-aware KB 2 indexer pipeline with permission metadata ingestion."""
    data_source_name = f"{index_name}-adls-source"
    skillset_name = f"{index_name}-content-understanding"
    indexer_name = f"{index_name}-adls-indexer"

    # KB 2 uses ADLS Gen2 data source with HNS and permission ingestion
    data_source = {
        "name": data_source_name,
        "type": "adlsgen2",
        "credentials": {"connectionString": f"ResourceId={storage_resource_id};"},
        "container": {"name": KB2_CONTAINER_NAME},
        "indexerPermissionOptions": ["userIds", "groupIds"],
    }

    skillset = {
        "name": skillset_name,
        "description": (
            "Semantic PDF chunking, image descriptions, and vectorization for "
            "KB 2 procurement with ACL support."
        ),
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
                    "maximumLength": 2000,
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
                        {
                            "name": "metadata_storage_path",
                            "source": "/document/metadata_storage_path",
                        },
                        # ACL metadata from ADLS Gen2 indexer
                        {"name": "user_ids", "source": "/document/metadata_user_ids"},
                        {"name": "group_ids", "source": "/document/metadata_group_ids"},
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
    """Replace the PDFs in the folder scoped to the KB 1 blob indexer."""
    account_url = f"https://{storage_account_name}.blob.core.windows.net"
    async with BlobServiceClient(account_url=account_url, credential=credential) as service:
        container = service.get_container_client(CONTAINER_NAME)
        stale_blobs = [
            blob.name
            async for blob in container.list_blobs(name_starts_with=f"{KB1_BLOB_PREFIX}/")
        ]
        for blob_name in stale_blobs:
            await container.delete_blob(blob_name)

        extracted_images = service.get_container_client(EXTRACTED_IMAGES_CONTAINER_NAME)
        try:
            image_blobs = [blob.name async for blob in extracted_images.list_blobs()]
            for blob_name in image_blobs:
                await extracted_images.delete_blob(blob_name)
        except ResourceNotFoundError:
            pass

        for pdf_path in pdfs:
            blob = container.get_blob_client(f"{KB1_BLOB_PREFIX}/{pdf_path.name}")
            with pdf_path.open("rb") as pdf_file:
                await blob.upload_blob(pdf_file, overwrite=True)
    return len(pdfs)


async def clear_index_documents(endpoint: str, index_name: str, credential: Any) -> int:
    """Delete projected chunks so removed source documents cannot remain searchable."""
    async with SearchClient(
        endpoint=endpoint,
        index_name=index_name,
        credential=credential,
    ) as search_client:
        try:
            results = await search_client.search(search_text="*", select=["chunk_id"])
            documents = [{"chunk_id": result["chunk_id"]} async for result in results]
        except ResourceNotFoundError:
            return 0

        for offset in range(0, len(documents), 1000):
            await search_client.delete_documents(documents=documents[offset : offset + 1000])
        return len(documents)


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


async def wait_for_indexer(
    client: SearchIndexerClient,
    indexer_name: str,
    started_after: datetime,
) -> tuple[int, int]:
    """Wait for the current indexer execution and return item/failure counts."""
    while True:
        indexer_status = await client.get_indexer_status(indexer_name)
        result = indexer_status.last_result
        if result is None or result.start_time is None or result.start_time < started_after:
            await asyncio.sleep(INDEXER_POLL_SECONDS)
            continue

        execution_status = getattr(result.status, "value", result.status)
        if execution_status == "success":
            if result.failed_item_count:
                raise RuntimeError(
                    f"Indexer '{indexer_name}' completed with "
                    f"{result.failed_item_count} failed items."
                )
            return result.item_count, result.failed_item_count
        if execution_status not in {"inProgress", "reset"}:
            raise RuntimeError(
                f"Indexer '{indexer_name}' ended with status '{execution_status}': "
                f"{result.error_message or 'No error message was returned.'}"
            )
        await asyncio.sleep(INDEXER_POLL_SECONDS)


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
    knowledge_sources = {source.name: KnowledgeSourceReference(name=source.name)}
    try:
        existing_knowledge_base = await client.get_knowledge_base(knowledge_base_name)
    except ResourceNotFoundError:
        pass
    else:
        knowledge_sources.update(
            {
                reference.name: reference
                for reference in existing_knowledge_base.knowledge_sources
            }
        )
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
        knowledge_sources=list(knowledge_sources.values()),
        retrieval_reasoning_effort=KnowledgeRetrievalLowReasoningEffort(),
        output_mode=KnowledgeRetrievalOutputMode.EXTRACTIVE_DATA,
    )
    await client.create_or_update_knowledge_base(knowledge_base=knowledge_base)


async def create_kb2_knowledge_base(
    client: SearchIndexClient,
    *,
    index_name: str,
    knowledge_base_name: str,
    openai_endpoint: str,
    model_deployment: str,
    model_name: str,
) -> None:
    """Create the KB 2 ACL-aware knowledge base for sourcing review."""
    source = SearchIndexKnowledgeSource(
        name=index_name,
        description=(
            "Caldova procurement sourcing documents including RFP, supplier responses, "
            "agreements, amendments, purchase orders, and evaluation evidence with "
            "document-level access control based on Entra group membership."
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
    knowledge_sources = {source.name: KnowledgeSourceReference(name=source.name)}
    try:
        existing_knowledge_base = await client.get_knowledge_base(knowledge_base_name)
    except ResourceNotFoundError:
        pass
    else:
        knowledge_sources.update(
            {
                reference.name: reference
                for reference in existing_knowledge_base.knowledge_sources
            }
        )
    knowledge_base = KnowledgeBase(
        name=knowledge_base_name,
        description=(
            "Sourcing review knowledge base with document-level access control "
            "for the LTG242 hosted agent."
        ),
        models=[
            KnowledgeBaseAzureOpenAIModel(
                azure_open_ai_parameters=AzureOpenAIVectorizerParameters(
                    resource_url=openai_endpoint,
                    deployment_name=model_deployment,
                    model_name=model_name,
                )
            )
        ],
        knowledge_sources=list(knowledge_sources.values()),
        retrieval_reasoning_effort=KnowledgeRetrievalLowReasoningEffort(),
        output_mode=KnowledgeRetrievalOutputMode.EXTRACTIVE_DATA,
    )
    await client.create_or_update_knowledge_base(knowledge_base=knowledge_base)


async def configure_kb2(
    *,
    endpoint: str,
    credential: Any,
    storage_resource_id: str,
    foundry_endpoint: str,
    openai_endpoint: str,
    model_deployment: str,
    model_name: str,
    embedding_deployment: str,
    embedding_model: str,
) -> None:
    """Create and run the ACL-aware KB 2 indexing pipeline."""
    index = build_kb2_acl_index(
        KB2_INDEX_NAME,
        openai_endpoint,
        embedding_deployment,
        embedding_model,
    )
    async with SearchIndexClient(endpoint=endpoint, credential=credential) as index_client:
        await index_client.create_or_update_index(index)
        removed_chunks = await clear_index_documents(
            endpoint,
            KB2_INDEX_NAME,
            credential,
        )
        await create_kb2_knowledge_base(
            index_client,
            index_name=KB2_INDEX_NAME,
            knowledge_base_name=KB2_KNOWLEDGE_BASE_NAME,
            openai_endpoint=openai_endpoint,
            model_deployment=model_deployment,
            model_name=model_name,
        )

    pipeline = build_kb2_indexer_payloads(
        index_name=KB2_INDEX_NAME,
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
        indexer_name = pipeline["indexers"][0]
        await indexer_client.reset_indexer(indexer_name)
        started_after = datetime.now(UTC) - timedelta(seconds=5)
        await indexer_client.run_indexer(indexer_name)
        indexed_items, failed_items = await wait_for_indexer(
            indexer_client,
            indexer_name,
            started_after,
        )

    print(
        f"Removed {removed_chunks} stale chunks and indexed {indexed_items} items "
        f"with {failed_items} failures for knowledge base "
        f"'{KB2_KNOWLEDGE_BASE_NAME}'."
    )


async def main_async() -> None:
    """Configure the KB 1 and ACL-aware KB 2 indexing pipelines."""
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
    kb2_storage_resource_id = os.environ["KB2_STORAGE_ACCOUNT_ID"]
    storage_resource_id = (
        f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}"
        f"/providers/Microsoft.Storage/storageAccounts/{storage_account_name}"
    )
    foundry_endpoint = f"https://{ai_account_name}.services.ai.azure.com"
    pdfs, provenance = find_kb1_pdfs()
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
            removed_chunks = await clear_index_documents(
                endpoint,
                SEARCH_INDEX_NAME,
                credential,
            )
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
            indexer_name = pipeline["indexers"][0]
            await indexer_client.reset_indexer(indexer_name)
            started_after = datetime.now(UTC) - timedelta(seconds=5)
            await indexer_client.run_indexer(indexer_name)
            indexed_items, failed_items = await wait_for_indexer(
                indexer_client,
                indexer_name,
                started_after,
            )

        print(
            f"Uploaded {uploaded} PDFs, removed {removed_chunks} stale chunks, "
            f"and indexed {indexed_items} items with {failed_items} failures "
            f"for knowledge base '{KNOWLEDGE_BASE_NAME}'. Source: "
            f"{provenance.get('repository', 'unknown')} at "
            f"{provenance.get('commit', 'unknown')}, corpus '{KB1_CORPUS_NAME}'."
        )
        await configure_kb2(
            endpoint=endpoint,
            credential=credential,
            storage_resource_id=kb2_storage_resource_id,
            foundry_endpoint=foundry_endpoint,
            openai_endpoint=openai_endpoint,
            model_deployment=model_deployment,
            model_name=model_name,
            embedding_deployment=embedding_deployment,
            embedding_model=embedding_model,
        )
    finally:
        await credential.close()


if __name__ == "__main__":
    asyncio.run(main_async())
