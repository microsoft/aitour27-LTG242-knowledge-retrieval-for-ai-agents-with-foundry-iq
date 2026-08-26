"""Find Entra group object IDs for the KB 2 ACL demonstration."""

import argparse
import asyncio
import os
from collections.abc import Sequence

from azure.identity.aio import AzureDeveloperCliCredential
from dotenv_azd import load_azd_env
from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph import GraphServiceClient
from msgraph.generated.groups.groups_request_builder import GroupsRequestBuilder

load_azd_env()

GRAPH_SCOPES = ["https://graph.microsoft.com/.default"]


def parse_args() -> argparse.Namespace:
    """Parse optional exact group names for automation."""
    parser = argparse.ArgumentParser(
        description=(
            "List Entra groups and current-user memberships for KB 2 ACL selection. "
            "Supply both names to emit the two environment assignments directly."
        )
    )
    parser.add_argument(
        "--member-group-name",
        default=os.getenv("SOURCING_MEMBER_GROUP_NAME"),
        help="Display name of the group containing the demo user.",
    )
    parser.add_argument(
        "--non-member-group-name",
        default=os.getenv("SOURCING_NON_MEMBER_GROUP_NAME"),
        help="Display name of the group that does not contain the demo user.",
    )
    args = parser.parse_args()
    if bool(args.member_group_name) != bool(args.non_member_group_name):
        parser.error("Specify both group names, or neither to list group candidates.")
    return args


def escape_odata_string(value: str) -> str:
    """Escape a value for use as an OData single-quoted string literal."""
    return value.replace("'", "''")


async def find_group_id(client: GraphServiceClient, display_name: str) -> str:
    """Return the unique Entra group ID matching an exact display name."""
    query_parameters = GroupsRequestBuilder.GroupsRequestBuilderGetQueryParameters(
        filter=f"displayName eq '{escape_odata_string(display_name)}'",
        select=["id", "displayName"],
    )
    request_configuration = RequestConfiguration(query_parameters=query_parameters)
    response = await client.groups.get(request_configuration=request_configuration)
    groups: Sequence[object] = response.value if response and response.value else []

    if not groups:
        raise RuntimeError(f"No Entra group found with display name: {display_name!r}")
    if len(groups) > 1:
        ids = ", ".join(str(group.id) for group in groups)
        raise RuntimeError(
            f"Multiple Entra groups found with display name {display_name!r}: {ids}. "
            "Use distinct group display names."
        )

    group_id = groups[0].id
    if not group_id:
        raise RuntimeError(f"Entra group {display_name!r} has no object ID.")
    return group_id


async def list_group_memberships(client: GraphServiceClient) -> dict[str, str]:
    """Return the signed-in user's transitive group memberships by object ID."""
    response = await client.me.transitive_member_of.graph_group.get()
    groups: Sequence[object] = response.value if response and response.value else []
    return {
        group.id: group.display_name or "<unnamed group>"
        for group in groups
        if group.id
    }


async def list_groups(client: GraphServiceClient) -> dict[str, str]:
    """Return directory groups by object ID, up to the Graph API page limit."""
    query_parameters = GroupsRequestBuilder.GroupsRequestBuilderGetQueryParameters(
        select=["id", "displayName"],
        top=999,
    )
    request_configuration = RequestConfiguration(query_parameters=query_parameters)
    response = await client.groups.get(request_configuration=request_configuration)
    groups: Sequence[object] = response.value if response and response.value else []
    return {
        group.id: group.display_name or "<unnamed group>"
        for group in groups
        if group.id
    }


def print_group_candidates(member_groups: dict[str, str], directory_groups: dict[str, str]) -> None:
    """Print each group ID, labeling memberships suitable for the member ACL."""
    if member_groups:
        print("Groups containing the signed-in user (member-group candidates):")
        sorted_member_groups = sorted(
            member_groups.items(), key=lambda item: item[1].lower()
        )
        for group_id, display_name in sorted_member_groups:
            print(f"  MEMBER     {display_name} ({group_id})")
    else:
        print("The signed-in user has no transitive Entra group memberships.")

    non_member_groups = {
        group_id: display_name
        for group_id, display_name in directory_groups.items()
        if group_id not in member_groups
    }
    if non_member_groups:
        print("\nGroups not containing the signed-in user (non-member-group candidates):")
        for group_id, display_name in sorted(
            non_member_groups.items(), key=lambda item: item[1].lower()
        ):
            print(f"  NON_MEMBER {display_name} ({group_id})")
    else:
        print("\nNo non-member group candidates were returned.")


async def main() -> None:
    """Authenticate with Azure Developer CLI and resolve or list the groups."""
    args = parse_args()
    credential = AzureDeveloperCliCredential()
    client = GraphServiceClient(credentials=credential, scopes=GRAPH_SCOPES)
    try:
        if args.member_group_name:
            member_group_id, non_member_group_id = await asyncio.gather(
                find_group_id(client, args.member_group_name),
                find_group_id(client, args.non_member_group_name),
            )
        else:
            member_groups, directory_groups = await asyncio.gather(
                list_group_memberships(client), list_groups(client)
            )
    finally:
        await credential.close()

    if args.member_group_name:
        print(f"azd env set SOURCING_MEMBER_GROUP_OID {member_group_id}")
        print(f"azd env set SOURCING_NON_MEMBER_GROUP_OID {non_member_group_id}")
    else:
        print_group_candidates(member_groups, directory_groups)


if __name__ == "__main__":
    asyncio.run(main())