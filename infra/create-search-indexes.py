"""Create an Azure AI Search index and knowledge base for the hosted agent."""

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from azure.identity.aio import AzureDeveloperCliCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.search.documents.indexes.models import (
    AzureOpenAIVectorizer,
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
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env", override=True)

DATA_DIR = Path("data/index-data")
INDEX_SCHEMA_PATH = DATA_DIR / "index.json"
RECORDS_PATH = DATA_DIR / "documents.jsonl"


async def create_index_and_upload(
    endpoint: str,
    credential: Any,
    index_name: str,
    openai_endpoint: str,
    embedding_deployment: str,
    embedding_model: str,
) -> int:
    """Create the configured index and upload JSONL records."""
    with INDEX_SCHEMA_PATH.open(encoding="utf-8") as schema_file:
        index = SearchIndex(json.load(schema_file))
    index.name = index_name

    if index.vector_search and index.vector_search.vectorizers:
        vectorizer = index.vector_search.vectorizers[0]
        if isinstance(vectorizer, AzureOpenAIVectorizer) and vectorizer.parameters:
            vectorizer.parameters.resource_url = openai_endpoint
            vectorizer.parameters.deployment_name = embedding_deployment
            vectorizer.parameters.model_name = embedding_model

    async with SearchIndexClient(endpoint=endpoint, credential=credential) as index_client:
        await index_client.create_or_update_index(index)

    records = []
    with RECORDS_PATH.open(encoding="utf-8") as records_file:
        for line_number, line in enumerate(records_file, start=1):
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as error:
                    raise ValueError(
                        f"Invalid JSON on line {line_number} of {RECORDS_PATH}"
                    ) from error

    async with SearchClient(
        endpoint=endpoint, index_name=index_name, credential=credential
    ) as search_client:
        for offset in range(0, len(records), 100):
            await search_client.upload_documents(documents=records[offset : offset + 100])
    return len(records)


async def main_async() -> None:
    """Create the index, knowledge source, and knowledge base."""
    missing = [path for path in (INDEX_SCHEMA_PATH, RECORDS_PATH) if not path.exists()]
    if missing:
        paths = ", ".join(str(path) for path in missing)
        raise FileNotFoundError(
            f"Add your retrieval data before provisioning. Missing: {paths}. "
            "See data/index-data/README.md."
        )

    endpoint = os.environ["AZURE_AI_SEARCH_SERVICE_ENDPOINT"]
    openai_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
    model_deployment = os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]
    model_name = os.environ["AZURE_OPENAI_CHATGPT_MODEL_NAME"]
    embedding_deployment = os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"]
    embedding_model = os.environ["AZURE_OPENAI_EMBEDDING_MODEL_NAME"]
    index_name = os.environ.get("AZURE_AI_SEARCH_INDEX_NAME", "session-documents")
    knowledge_base_name = os.environ.get(
        "AZURE_AI_SEARCH_KNOWLEDGE_BASE_NAME", "knowledge-retrieval-kb"
    )
    credential = AzureDeveloperCliCredential(tenant_id=os.environ["AZURE_TENANT_ID"])

    try:
        uploaded = await create_index_and_upload(
            endpoint,
            credential,
            index_name,
            openai_endpoint,
            embedding_deployment,
            embedding_model,
        )
        async with SearchIndexClient(endpoint=endpoint, credential=credential) as client:
            source = SearchIndexKnowledgeSource(
                name=index_name,
                description="Session-provided documents for grounded retrieval.",
                search_index_parameters=SearchIndexKnowledgeSourceParameters(
                    search_index_name=index_name,
                    source_data_fields=[
                        SearchIndexFieldReference(name="uid"),
                        SearchIndexFieldReference(name="snippet"),
                        SearchIndexFieldReference(name="blob_path"),
                        SearchIndexFieldReference(name="snippet_parent_id"),
                    ],
                    search_fields=[SearchIndexFieldReference(name="snippet")],
                    semantic_configuration_name="semantic-configuration",
                ),
            )
            await client.create_or_update_knowledge_source(knowledge_source=source)
            knowledge_base = KnowledgeBase(
                name=knowledge_base_name,
                description="Knowledge retrieval source for the LTG242 hosted agent.",
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
        print(f"Uploaded {uploaded} documents and created '{knowledge_base_name}'.")
    finally:
        await credential.close()


if __name__ == "__main__":
    asyncio.run(main_async())
