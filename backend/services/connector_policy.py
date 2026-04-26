from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple


POLICY_FILE = Path(__file__).resolve().parents[1] / "data" / "connector_conflict_policy.json"


def load_connector_policy() -> dict:
    default_policy = {
        "merge": "source_of_truth",
        "plaid": "source_of_truth",
        "cloud_costs": "latest_timestamp_wins",
    }
    if not POLICY_FILE.exists():
        return default_policy
    try:
        with POLICY_FILE.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
            return {
                "merge": payload.get("merge", default_policy["merge"]),
                "plaid": payload.get("plaid", default_policy["plaid"]),
                "cloud_costs": payload.get("cloud_costs", default_policy["cloud_costs"]),
            }
    except Exception:
        return default_policy


def save_connector_policy(policy: dict) -> None:
    POLICY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with POLICY_FILE.open("w", encoding="utf-8") as handle:
        json.dump(policy, handle, indent=2, sort_keys=True)


def parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        clean = value.replace("Z", "+00:00")
        return datetime.fromisoformat(clean)
    except Exception:
        return None


def should_apply_connector_update(
    policy: str,
    connector: str,
    incoming_ts: Optional[datetime],
    local_updated_at: Optional[datetime],
    local_remote_modified_at: Optional[datetime],
    local_source: Optional[str] = None,
) -> Tuple[bool, str]:
    if policy == "source_of_truth":
        return True, "connector_source_of_truth"

    if policy == "latest_timestamp_wins":
        if incoming_ts and local_remote_modified_at and incoming_ts <= local_remote_modified_at:
            return False, "stale_remote_payload"
        return True, "latest_timestamp_wins"

    # manual_review policy
    if local_source and local_source not in {"", connector, None}:
        return False, "source_conflict_requires_manual_review"

    if local_updated_at and local_remote_modified_at and local_updated_at > local_remote_modified_at:
        return False, "local_override_requires_manual_review"

    if incoming_ts and local_remote_modified_at and incoming_ts <= local_remote_modified_at:
        return False, "stale_remote_payload"

    return True, "manual_review_passed"
