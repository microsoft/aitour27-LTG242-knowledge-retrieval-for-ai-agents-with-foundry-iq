"""Upload procurement PDFs and apply Entra group-based ACLs for KB 2."""

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from azure.core.exceptions import ResourceExistsError
from azure.identity.aio import AzureDeveloperCliCredential
from azure.storage.filedatalake.aio import (
    DataLakeDirectoryClient,
    DataLakeServiceClient,
    FileSystemClient,
)
from dotenv_azd import load_azd_env

load_azd_env()

REPO_ROOT = Path(__file__).parents[1]
SAMPLE_DATA_ROOT = REPO_ROOT / "sample-data"
CORPORA_PATH = SAMPLE_DATA_ROOT / "corpora.json"
KB2_CORPUS_NAMES = ["procurement", "policy-and-diagrams"]
KB2_EXPECTED_PDF_COUNT = 12  # 9 procurement + 3 policy-and-diagrams
CONTAINER_NAME = "kb2-sourcing"

# ACL directory structure
SHARED_PREFIX = "shared"
EVALUATOR_PREFIX = "evaluator"
MEMBER_DOCUMENTS = {
    "RSP-SUM-2026-01.pdf",
    "MSA-CAL-SUM-2024-017.pdf",
}
NON_MEMBER_DOCUMENTS = {
    "RSP-AST-2026-01.pdf",
    "RSP-ATL-2026-01.pdf",
    "MSA-CAL-AST-2024-011.pdf",
    "MSA-CAL-ATL-2025-004.pdf",
}
CONFIDENTIAL_DOCUMENTS = {
    "AMD-MSA-SUM-2026-01.pdf",
    "PO-CAL-SUM-2026-1108.pdf",
}


async def find_kb2_pdfs() -> dict[str, list[Path]]:
    """Return the manifest-selected KB 2 PDFs by corpus."""
    try:
        corpora = json.loads(CORPORA_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as error:
        raise RuntimeError(
            "The sample-data snapshot is missing or invalid. "
            "Run 'uv run python scripts/sync_sample_data.py'."
        ) from error

    pdf_by_corpus = {}
    total_count = 0
    for corpus_name in KB2_CORPUS_NAMES:
        if corpus_name not in corpora:
            raise RuntimeError(f"Corpus '{corpus_name}' not found in corpora.json.")
        relative_paths = corpora[corpus_name]
        if not isinstance(relative_paths, list) or not all(
            isinstance(relative_path, str) for relative_path in relative_paths
        ):
            raise RuntimeError(f"Corpus '{corpus_name}' must be a list of PDF paths.")

        pdfs = [SAMPLE_DATA_ROOT / relative_path for relative_path in relative_paths]
        missing = [str(pdf.relative_to(REPO_ROOT)) for pdf in pdfs if not pdf.is_file()]
        if missing:
            raise RuntimeError(f"Missing KB 2 PDFs: {missing}")
        pdf_by_corpus[corpus_name] = pdfs
        total_count += len(pdfs)

    if total_count != KB2_EXPECTED_PDF_COUNT:
        raise RuntimeError(
            f"Expected {KB2_EXPECTED_PDF_COUNT} KB 2 PDFs, found {total_count}."
        )
    return pdf_by_corpus


async def setup_acl_directories(
    file_system_client: FileSystemClient,
    member_group_oid: str,
    non_member_group_oid: str,
) -> tuple[DataLakeDirectoryClient, DataLakeDirectoryClient]:
    """Create ACL-controlled directories and return shared and evaluator clients."""
    root_dir = file_system_client.get_directory_client("/")
    root_acl = (
        f"user::rwx,"
        f"group::---,"
        f"group:{member_group_oid}:r-x,"
        f"group:{non_member_group_oid}:r-x,"
        f"mask::r-x,"
        f"other::---"
    )
    await root_dir.set_access_control(acl=root_acl)

    # Create shared directory with member and non-member groups readable
    shared_dir = file_system_client.get_directory_client(SHARED_PREFIX)
    try:
        await shared_dir.create_directory()
    except ResourceExistsError:
        pass

    # Set ACL on shared directory: allow both groups to read
    shared_acl = (
        f"user::rwx,"
        f"group::---,"
        f"group:{member_group_oid}:r-x,"
        f"group:{non_member_group_oid}:r-x,"
        f"mask::r-x,"
        f"other::---"
    )
    await shared_dir.set_access_control_recursive(acl=shared_acl)

    # Create evaluator directory (restricted to member group only)
    evaluator_dir = file_system_client.get_directory_client(EVALUATOR_PREFIX)
    try:
        await evaluator_dir.create_directory()
    except ResourceExistsError:
        pass

    # Set ACL on evaluator directory: member group only
    evaluator_acl = (
        f"user::rwx,"
        f"group::---,"
        f"group:{member_group_oid}:r-x,"
        f"mask::r-x,"
        f"other::---"
    )
    await evaluator_dir.set_access_control_recursive(acl=evaluator_acl)

    return shared_dir, evaluator_dir


async def upload_and_acl_pdf(
    directory_client: DataLakeDirectoryClient,
    pdf_path: Path,
    acl_groups: list[str],
) -> None:
    """Upload a PDF and apply group-based ACLs."""
    file_client = directory_client.get_file_client(pdf_path.name)
    with pdf_path.open("rb") as pdf_file:
        await file_client.upload_data(pdf_file.read(), overwrite=True)

    # Apply ACLs with groups. Format: user::rwx,group:OID:r--,other::---
    acl_entries = "user::rw-,group::---"
    for group_oid in acl_groups:
        acl_entries += f",group:{group_oid}:r--"
    if acl_groups:
        acl_entries += ",mask::r--"
    acl_entries += ",other::---"
    await file_client.set_access_control(acl=acl_entries)


async def upload_kb2_pdfs(
    storage_account_name: str,
    credential: Any,
    member_group_oid: str,
    non_member_group_oid: str,
    pdf_by_corpus: dict[str, list[Path]],
) -> int:
    """Upload KB 2 PDFs and apply ACLs."""
    service_url = f"https://{storage_account_name}.dfs.core.windows.net"
    async with DataLakeServiceClient(account_url=service_url, credential=credential) as service:
        file_system_client = service.get_file_system_client(CONTAINER_NAME)

        # Create ACL-controlled directories
        shared_dir, evaluator_dir = await setup_acl_directories(
            file_system_client, member_group_oid, non_member_group_oid
        )

        # Upload and ACL policy and procurement overview (shared access)
        policy_pdfs = pdf_by_corpus.get("policy-and-diagrams", [])
        for pdf_path in policy_pdfs:
            acl_groups = [member_group_oid, non_member_group_oid]
            await upload_and_acl_pdf(shared_dir, pdf_path, acl_groups)
            print(f"Uploaded and ACL'd {pdf_path.name} to shared/ (accessible to both groups)")

        # Upload procurement PDFs to evaluator directory (restricted)
        procurement_pdfs = pdf_by_corpus.get("procurement", [])
        # First two are RFP and purchasing policy (shared)
        if len(procurement_pdfs) > 0:
            rfp_pdf = procurement_pdfs[0]
            acl_groups = [member_group_oid, non_member_group_oid]
            await upload_and_acl_pdf(shared_dir, rfp_pdf, acl_groups)
            print(f"Uploaded and ACL'd {rfp_pdf.name} to shared/ (RFP accessible to all)")

        # Remaining procurement PDFs to evaluator (restricted based on bidder)
        for pdf_path in procurement_pdfs[1:]:
            if pdf_path.name in MEMBER_DOCUMENTS:
                acl_groups = [member_group_oid]
                print(
                    f"Uploaded and ACL'd {pdf_path.name} to evaluator/ "
                    f"(Summit Dose - member group only)"
                )
            elif pdf_path.name in NON_MEMBER_DOCUMENTS:
                acl_groups = [non_member_group_oid]
                print(
                    f"Uploaded and ACL'd {pdf_path.name} to evaluator/ "
                    f"(Other bidder - non-member group only)"
                )
            elif pdf_path.name in CONFIDENTIAL_DOCUMENTS:
                acl_groups = []
                print(
                    f"Uploaded and ACL'd {pdf_path.name} to evaluator/ "
                    f"(Confidential - no group access)"
                )
            else:
                raise RuntimeError(f"No ACL classification for {pdf_path.name}.")
            await upload_and_acl_pdf(evaluator_dir, pdf_path, acl_groups)

        return len(procurement_pdfs) + len(policy_pdfs)


async def discover_group_oids() -> tuple[str, str]:
    """Discover or prompt for member and non-member group OIDs."""
    member_oid = os.environ.get("SOURCING_MEMBER_GROUP_OID", "").strip()
    non_member_oid = os.environ.get("SOURCING_NON_MEMBER_GROUP_OID", "").strip()

    if member_oid and non_member_oid:
        print("Using configured group OIDs from environment variables.")
        return member_oid, non_member_oid

    print("Group OID configuration required.")
    print("Set SOURCING_MEMBER_GROUP_OID and SOURCING_NON_MEMBER_GROUP_OID environment variables.")
    print(
        "Member group: Entra group containing the provisioning user "
        "(for Summit Dose representative access)"
    )
    print("Non-member group: Entra group NOT containing the provisioning user")
    raise RuntimeError(
        "SOURCING_MEMBER_GROUP_OID and SOURCING_NON_MEMBER_GROUP_OID must be set "
        "in the selected azd environment."
    )


async def main_async() -> None:
    """Upload KB 2 PDFs and apply Entra group-based ACLs."""
    storage_account_name = os.environ.get("KB2_STORAGE_ACCOUNT_NAME", "").strip()
    if not storage_account_name:
        raise RuntimeError("KB2_STORAGE_ACCOUNT_NAME environment variable not set.")

    member_group_oid, non_member_group_oid = await discover_group_oids()
    pdf_by_corpus = await find_kb2_pdfs()
    credential = AzureDeveloperCliCredential(tenant_id=os.environ["AZURE_TENANT_ID"])

    try:
        uploaded = await upload_kb2_pdfs(
            storage_account_name,
            credential,
            member_group_oid,
            non_member_group_oid,
            pdf_by_corpus,
        )
        print(
            f"Successfully uploaded {uploaded} KB 2 PDFs and applied Entra group-based ACLs. "
            f"Member group: {member_group_oid}, Non-member group: {non_member_group_oid}"
        )
    finally:
        await credential.close()


if __name__ == "__main__":
    asyncio.run(main_async())
