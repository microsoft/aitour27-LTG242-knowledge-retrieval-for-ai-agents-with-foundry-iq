"""Write provisioned Foundry settings to the repository root .env file."""

import os
from pathlib import Path

from dotenv import set_key

REPO_ROOT = Path(__file__).parents[1]
ENV_PATH = REPO_ROOT / ".env"


def main() -> None:
    """Write the azd outputs needed by local provisioning and agent runs."""
    required_keys = (
        "AZURE_TENANT_ID",
        "AZURE_SUBSCRIPTION_ID",
        "AZURE_RESOURCE_GROUP",
        "AZURE_LOCATION",
        "FOUNDRY_PROJECT_ENDPOINT",
        "AZURE_AI_PROJECT_ENDPOINT",
        "AZURE_AI_PROJECT_ID",
        "AZURE_AI_MODEL_DEPLOYMENT_NAME",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_CHATGPT_MODEL_NAME",
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
        "AZURE_OPENAI_EMBEDDING_MODEL_NAME",
        "AZURE_AI_SEARCH_SERVICE_ENDPOINT",
        "AZURE_AI_SEARCH_SERVICE_NAME",
    )
    missing = [key for key in required_keys if not os.environ.get(key)]
    if missing:
        raise RuntimeError(f"Missing required azd outputs: {', '.join(missing)}")

    values = {key: os.environ[key] for key in required_keys}
    values.update(
        {
            "AZURE_AI_SEARCH_INDEX_NAME": "session-documents",
            "AZURE_AI_SEARCH_KNOWLEDGE_BASE_NAME": "knowledge-retrieval-kb",
            "AZURE_AI_SEARCH_KB_MCP_CONNECTION_NAME": "knowledge-base-mcp-connection",
            "CUSTOM_FOUNDRY_AGENT_TOOLBOX_NAME": "knowledge-retrieval-tools",
            "APPLICATIONINSIGHTS_CONNECTION_STRING": os.environ.get(
                "APPLICATIONINSIGHTS_CONNECTION_STRING", ""
            ),
        }
    )

    ENV_PATH.touch()
    for key, value in values.items():
        set_key(ENV_PATH, key, value, quote_mode="never")

    print(f"Created {ENV_PATH}")


if __name__ == "__main__":
    main()
