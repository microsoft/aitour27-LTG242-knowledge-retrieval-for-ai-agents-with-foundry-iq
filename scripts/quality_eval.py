"""Evaluate hosted-agent response completeness against four ground-truth answers."""

import json
import os
import time
from pathlib import Path
from typing import Any

from azure.ai.projects import AIProjectClient
from azure.identity import AzureDeveloperCliCredential
from dotenv_azd import load_azd_env

REPO_ROOT = Path(__file__).parents[1]
load_azd_env()

AGENT_ROOT = REPO_ROOT / "src" / "agent-toolbox-foundryiq"
DATASET_PATH = (
    AGENT_ROOT / ".foundry" / "datasets" / "response_completeness_ground_truth.jsonl"
)
ENVIRONMENT_NAME = os.environ.get("AZURE_ENV_NAME", "pf-ltg242")
RESULTS_ROOT = AGENT_ROOT / ".foundry" / "results" / ENVIRONMENT_NAME
RUN_STATE_PATH = RESULTS_ROOT / "response_completeness_last_run.json"
AGENT_NAME = os.environ.get(
    "AGENT_INVOICE_INVESTIGATION_AGENT_NAME",
    "invoice-investigation-agent",
)
EXPECTED_CASE_COUNT = 4


def serialize(value: Any) -> Any:
    """Convert an SDK model into JSON-compatible data."""
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return str(value)


def write_json(path: Path, value: Any) -> None:
    """Write an evaluation artifact as formatted JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    """Run Response Completeness against the latest hosted-agent version."""
    dataset_rows = [
        json.loads(line)
        for line in DATASET_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(dataset_rows) != EXPECTED_CASE_COUNT:
        raise RuntimeError(
            f"Expected {EXPECTED_CASE_COUNT} evaluation cases, found {len(dataset_rows)}."
        )

    project_endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    model_deployment = os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]
    credential = AzureDeveloperCliCredential(
        tenant_id=os.environ["AZURE_TENANT_ID"],
        process_timeout=60,
    )
    project_client = AIProjectClient(endpoint=project_endpoint, credential=credential)

    try:
        agent = project_client.agents.get(agent_name=AGENT_NAME)
        agent_version = agent.versions["latest"]
        print(f"Agent: {agent_version.name} version {agent_version.version}")

        dataset = project_client.datasets.upload_file(
            name=f"{AGENT_NAME}-response-completeness-ground-truth",
            version=str(int(time.time())),
            file_path=str(DATASET_PATH),
        )
        print(f"Uploaded dataset: {dataset.id}")

        openai_client = project_client.get_openai_client()
        evaluation = openai_client.evals.create(
            name=f"Response Completeness - {AGENT_NAME}",
            data_source_config={
                "type": "custom",
                "item_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "ground_truth": {"type": "string"},
                    },
                    "required": ["query", "ground_truth"],
                },
                "include_sample_schema": True,
            },
            testing_criteria=[
                {
                    "type": "azure_ai_evaluator",
                    "name": "Response Completeness",
                    "evaluator_name": "builtin.response_completeness",
                    "data_mapping": {
                        "ground_truth": "{{item.ground_truth}}",
                        "response": "{{sample.output_text}}",
                    },
                    "initialization_parameters": {
                        "deployment_name": model_deployment,
                    },
                }
            ],
        )
        eval_run = openai_client.evals.runs.create(
            eval_id=evaluation.id,
            name=f"Response Completeness - {AGENT_NAME} v{agent_version.version}",
            data_source={
                "type": "azure_ai_target_completions",
                "source": {"type": "file_id", "id": dataset.id},
                "input_messages": {
                    "type": "template",
                    "template": [
                        {
                            "type": "message",
                            "role": "user",
                            "content": {
                                "type": "input_text",
                                "text": "{{item.query}}",
                            },
                        }
                    ],
                },
                "target": {
                    "type": "azure_ai_agent",
                    "name": AGENT_NAME,
                    "version": str(agent_version.version),
                },
            },
        )
        run_state = {
            "evalId": evaluation.id,
            "evalRunId": eval_run.id,
            "runName": eval_run.name,
            "agentName": AGENT_NAME,
            "agentVersion": str(agent_version.version),
            "datasetId": dataset.id,
            "startedAt": int(time.time()),
        }
        write_json(RUN_STATE_PATH, run_state)
        print(f"Evaluation run: {eval_run.id} ({eval_run.status})")

        while eval_run.status not in {"completed", "failed", "canceled"}:
            time.sleep(10)
            eval_run = openai_client.evals.runs.retrieve(
                run_id=eval_run.id,
                eval_id=evaluation.id,
            )
            print(f"Status: {eval_run.status}")

        run_state["status"] = eval_run.status
        run_state["completedAt"] = int(time.time())
        if getattr(eval_run, "report_url", None):
            run_state["reportUrl"] = eval_run.report_url
        write_json(RUN_STATE_PATH, run_state)

        if eval_run.status != "completed":
            raise RuntimeError(f"Evaluation ended with status '{eval_run.status}'.")

        output_items = list(
            openai_client.evals.runs.output_items.list(
                run_id=eval_run.id,
                eval_id=evaluation.id,
            )
        )
        output_path = RESULTS_ROOT / evaluation.id / f"{eval_run.id}.json"
        write_json(output_path, [serialize(item) for item in output_items])
        if len(output_items) != EXPECTED_CASE_COUNT:
            raise RuntimeError(
                f"Expected {EXPECTED_CASE_COUNT} output items, found {len(output_items)}."
            )
        print(f"Saved {len(output_items)} output items to {output_path}")
        if getattr(eval_run, "report_url", None):
            print(f"Report: {eval_run.report_url}")
    finally:
        credential.close()


if __name__ == "__main__":
    main()