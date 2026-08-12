"""Grant Azure AI Search access to the deployed hosted-agent identity."""

import json
import os
import subprocess
import uuid

from azure.core.exceptions import HttpResponseError
from azure.identity import AzureDeveloperCliCredential
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.authorization.models import RoleAssignmentCreateParameters
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env", override=True)

AGENT_NAME = "agent-toolbox-foundryiq"
SEARCH_DATA_CONTRIBUTOR_ROLE_ID = "8ebe5a00-799e-43f5-93ac-243d3dce84a7"


def main() -> None:
    """Assign Search Index Data Contributor to the hosted agent identity."""
    command_env = os.environ.copy()
    command_env["AZURE_DEV_USER_AGENT"] = "microsoft_foundry_skill"
    result = subprocess.run(
        ["azd", "ai", "agent", "show", AGENT_NAME, "--output", "json", "--no-prompt"],
        check=True,
        capture_output=True,
        text=True,
        env=command_env,
    )
    agent = json.loads(result.stdout)
    principal_id = agent.get("instance_identity", {}).get("principal_id")
    if not principal_id:
        raise RuntimeError(f"Could not retrieve the hosted identity for {AGENT_NAME}.")

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
    assignment_name = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"{scope}:{principal_id}:{SEARCH_DATA_CONTRIBUTOR_ROLE_ID}",
        )
    )
    credential = AzureDeveloperCliCredential(tenant_id=os.environ["AZURE_TENANT_ID"])
    client = AuthorizationManagementClient(credential, subscription_id)
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
        print(f"Search access is already assigned to {AGENT_NAME}.")
    else:
        print(f"Assigned Search Index Data Contributor to {AGENT_NAME}.")


if __name__ == "__main__":
    main()
