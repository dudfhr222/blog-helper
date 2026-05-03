"""State helpers for design_agent verification gates.

Manages two JSON files in outputs/design/state/:
- last_run.json: single source of truth for the most recent dry-run/apply.
  The agent must read this file and only report success when gates_passed=true.
- pending_manual.json: queue of automation failures that require manual apply.
  The agent must drain this queue before starting new work.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
STATE_DIR = PROJECT_ROOT / "outputs" / "design" / "state"
LAST_RUN_PATH = STATE_DIR / "last_run.json"
PENDING_MANUAL_PATH = STATE_DIR / "pending_manual.json"

GATE_KEYS = (
    "backup_exists",
    "tokens_preserved",
    "sidebar_components_present",
    "css_base_preserved",
    "css_specificity_ok",
    "dry_run_executed",
    "screenshot_captured",
    "user_visual_ok",
    "save_confirmed",
)


def _ensure_dir() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def new_run_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def init_last_run(run_id: str, mode: str) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "mode": mode,
        "gates_passed": False,
        "gates": {key: None for key in GATE_KEYS},
        "errors": [],
        "warnings": [],
        "artifacts": {},
        "next_action": "block_report",
        "updated_at": datetime.now().isoformat(),
    }


def write_last_run(payload: dict[str, Any]) -> Path:
    _ensure_dir()
    payload["updated_at"] = datetime.now().isoformat()
    payload["gates_passed"] = _evaluate_gates_passed(payload)
    LAST_RUN_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return LAST_RUN_PATH


def read_last_run() -> dict[str, Any] | None:
    if not LAST_RUN_PATH.exists():
        return None
    return json.loads(LAST_RUN_PATH.read_text(encoding="utf-8"))


def _evaluate_gates_passed(payload: dict[str, Any]) -> bool:
    """Determine gates_passed based on mode and gate values.

    apply mode requires every gate true. dry_run mode treats save_confirmed/
    user_visual_ok as not-yet-required (null is acceptable).
    """
    gates = payload.get("gates", {})
    mode = payload.get("mode", "dry_run")
    required: list[str]
    if mode == "apply":
        required = list(GATE_KEYS)
    else:
        required = [k for k in GATE_KEYS if k not in ("save_confirmed", "user_visual_ok")]
    for key in required:
        if gates.get(key) is not True:
            return False
    return True


def set_gate(payload: dict[str, Any], key: str, value: bool | None) -> None:
    if key not in GATE_KEYS:
        raise KeyError(f"unknown gate key: {key}")
    payload.setdefault("gates", {})[key] = value


def add_errors(payload: dict[str, Any], errors: list[str]) -> None:
    payload.setdefault("errors", []).extend(errors)


def add_warnings(payload: dict[str, Any], warnings: list[str]) -> None:
    payload.setdefault("warnings", []).extend(warnings)


def set_artifacts(payload: dict[str, Any], **paths: str) -> None:
    payload.setdefault("artifacts", {}).update({k: v for k, v in paths.items() if v})


def set_next_action(payload: dict[str, Any], action: str) -> None:
    valid = {"block_report", "require_user_visual", "apply", "pending_manual", "done"}
    if action not in valid:
        raise ValueError(f"invalid next_action: {action}")
    payload["next_action"] = action


def mark_user_visual(ok: bool) -> dict[str, Any]:
    """Update last_run.json after user confirms screenshots visually.

    Returns the updated payload. Raises if last_run.json missing.
    """
    payload = read_last_run()
    if payload is None:
        raise FileNotFoundError("last_run.json not found; nothing to confirm")
    set_gate(payload, "user_visual_ok", ok)
    if ok:
        set_next_action(payload, "apply")
    else:
        set_next_action(payload, "block_report")
        add_errors(payload, ["user_visual_ok=false: visual review rejected by user"])
    write_last_run(payload)
    return payload


def _read_pending() -> dict[str, Any]:
    if not PENDING_MANUAL_PATH.exists():
        return {"queue": []}
    return json.loads(PENDING_MANUAL_PATH.read_text(encoding="utf-8"))


def push_pending_manual(run_id: str, target: str, file_path: str, reason: str) -> Path:
    _ensure_dir()
    data = _read_pending()
    data.setdefault("queue", []).append(
        {
            "run_id": run_id,
            "target": target,
            "file_path": file_path,
            "reason": reason,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
        }
    )
    PENDING_MANUAL_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return PENDING_MANUAL_PATH


def list_pending_manual() -> list[dict[str, Any]]:
    return [item for item in _read_pending().get("queue", []) if item.get("status") == "pending"]


def resolve_pending_manual(run_id: str) -> bool:
    data = _read_pending()
    changed = False
    for item in data.get("queue", []):
        if item.get("run_id") == run_id and item.get("status") == "pending":
            item["status"] = "resolved"
            item["resolved_at"] = datetime.now().isoformat()
            changed = True
    if changed:
        PENDING_MANUAL_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return changed
