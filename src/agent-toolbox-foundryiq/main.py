"""Hosted agent that accesses Foundry IQ through a Foundry toolbox."""

import logging
import os
from collections.abc import Awaitable, Callable

from agent_framework import Agent, ChatContext, ChatResponse, Message
from agent_framework.foundry import FoundryChatClient
from agent_framework.observability import enable_instrumentation
from agent_framework_foundry_hosting import FoundryToolbox, ResponsesHostServer
from agent_framework_openai import OpenAIContentFilterException
from azure.identity import AzureDeveloperCliCredential, ManagedIdentityCredential
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env", override=True)

logger = logging.getLogger("agent-toolbox-foundryiq")

PROJECT_ENDPOINT = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
MODEL_DEPLOYMENT_NAME = os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]
AGENT_SCENARIO = os.environ.get("AGENT_SCENARIO", "invoice-investigation")
AGENT_CONFIGS = {
    "invoice-investigation": {
        "name": "InvoiceInvestigationAgent",
        "toolbox": "knowledge-retrieval-tools",
        "instructions": (
            "You are Caldova's Invoice Investigation Agent. Always use the knowledge-base "
            "tool before answering and rely only on facts returned by that tool. Cite every "
            "material claim inline using the retrieved document title and page number when "
            "available. Never infer a charge, total, disposition, or supply decision from "
            "missing evidence. For calculations, pass only retrieved values to code "
            "interpreter and show the arithmetic. When the user asks for a chart, plot, "
            "timeline, or other visual, use code interpreter and return the generated "
            "artifact with the grounded answer. Distinguish conditional approval from a "
            "general restriction and state the exact affected equipment or runs. If the "
            "tools do not provide enough information, identify the missing evidence and say "
            "that you cannot fully answer the question."
        ),
    },
    "supplier-intelligence": {
        "name": "SupplierIntelligenceAgent",
        "toolbox": "supplier-intelligence-tools",
        "instructions": (
            "You are Caldova's Supplier Intelligence Agent. Always use the knowledge-base "
            "tool before answering and rely only on facts returned by that tool. Treat records "
            "from the Caldova suppliers database as current structured operational facts and "
            "include their as-of dates "
            "when available. Clearly distinguish signed document commitments from current "
            "Caldova suppliers database facts whenever both are returned. In user-facing prose "
            "and headings, always call this source the 'Caldova suppliers database'; do not "
            "call it MCP or PostgreSQL. Preserve technical source identifiers only inside "
            "citations. When an answer requires joining sources, "
            "use identifiers or canonical names found in documents to retrieve the related "
            "database records. Resolve entity relationships, such as substance-to-product or "
            "manufacturer-to-substance mappings, from explicit database relationship records; "
            "never infer them from document co-occurrence. Retrieve every relationship needed "
            "to answer the question before concluding evidence is missing. Cite every material "
            "claim using the retrieved title or source identifier and attribute cross-source "
            "claims to the source that establishes each part of the relationship. Never infer "
            "supplier status, capacity, performance, audit findings, or quality risk from "
            "missing data. For comparisons and calculations, pass only retrieved values to "
            "code interpreter and show the method. If the tools do not provide enough "
            "information, identify the missing evidence and say that you cannot fully answer "
            "the question."
        ),
    },
}
if AGENT_SCENARIO not in AGENT_CONFIGS:
    raise RuntimeError(f"Unknown AGENT_SCENARIO: {AGENT_SCENARIO}")
AGENT_CONFIG = AGENT_CONFIGS[AGENT_SCENARIO]
TOOLBOX_NAME = os.environ.get(
    "CUSTOM_FOUNDRY_AGENT_TOOLBOX_NAME",
    AGENT_CONFIG["toolbox"],
)
CONTENT_FILTER_MESSAGE = (
    "I can't help with that request because it violates content safety policies. "
    "If you have a safer version of the question, I can help with that instead."
)


async def content_filter_middleware(
    context: ChatContext, call_next: Callable[[], Awaitable[None]]
) -> None:
    """Convert model-side content-filter blocks into a clear response."""
    try:
        await call_next()
    except OpenAIContentFilterException:
        context.result = ChatResponse(
            messages=Message("assistant", [CONTENT_FILTER_MESSAGE]),
            finish_reason="stop",
        )


def main() -> None:
    """Run the toolbox-backed agent as a Responses server."""
    credential = (
        ManagedIdentityCredential()
        if "FOUNDRY_HOSTING_ENVIRONMENT" in os.environ
        else AzureDeveloperCliCredential(
            tenant_id=os.environ["AZURE_TENANT_ID"],
            process_timeout=60,
        )
    )
    toolbox_endpoint = f"{PROJECT_ENDPOINT.rstrip('/')}/toolboxes/{TOOLBOX_NAME}/mcp?api-version=v1"
    toolbox = FoundryToolbox(
        credential=credential,
        url=toolbox_endpoint,
        load_prompts=False,
    )
    client = FoundryChatClient(
        project_endpoint=PROJECT_ENDPOINT,
        model=MODEL_DEPLOYMENT_NAME,
        credential=credential,
        middleware=[content_filter_middleware],
    )
    agent = Agent(
        client=client,
        name=AGENT_CONFIG["name"],
        instructions=AGENT_CONFIG["instructions"],
        tools=[toolbox],
        default_options={"store": False},
    )
    ResponsesHostServer(agent).run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    enable_instrumentation(enable_sensitive_data=True)
    main()
