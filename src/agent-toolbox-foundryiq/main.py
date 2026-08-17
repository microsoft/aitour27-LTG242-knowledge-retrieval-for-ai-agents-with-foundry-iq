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
TOOLBOX_NAME = os.environ.get("CUSTOM_FOUNDRY_AGENT_TOOLBOX_NAME", "knowledge-retrieval-tools")
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
        name="InvoiceInvestigationAgent",
        instructions=(
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
        tools=[toolbox],
        default_options={"store": False},
    )
    ResponsesHostServer(agent).run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    enable_instrumentation(enable_sensitive_data=True)
    main()
