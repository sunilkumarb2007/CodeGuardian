"""Bounded end-to-end check for the Demo Mode API.

Runs one investigation against an already running backend, waits for the
human approval gate, approves it and verifies the delivered result.
The server is never started by this script.

Usage: python scripts/run_demo_e2e_check.py [base_url]
"""
import sys
import time

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
REPO = "https://github.com/sunilkumarb2007/JavaAPICheck"
MAX_POLLS = 60
POLL_INTERVAL = 1.0


def poll_until(client: httpx.Client, run_id: str, predicate) -> dict:
    for _ in range(MAX_POLLS):
        workspace = client.get(f"{BASE}/api/runs/{run_id}/workspace").json()
        if predicate(workspace):
            return workspace
        time.sleep(POLL_INTERVAL)
    raise SystemExit(f"Timed out waiting for run {run_id}")


def main() -> int:
    with httpx.Client(timeout=10.0) as client:
        health = client.get(f"{BASE}/health").json()
        print("health:", health)

        started = client.post(f"{BASE}/api/demo/run", json={"repository_url": REPO}).json()
        run_id = started["run_id"]
        print("run:", run_id)

        ws = poll_until(client, run_id, lambda w: w["run"]["status"] == "waiting_for_approval")
        print("stopped at:", ws["run"]["current_stage"], "/", ws["run"]["status"])
        assert ws["incident"]["fingerprint"] == "NULL_OBJECT_ACCESS", ws["incident"]
        assert ws["evidence"], "no evidence"
        assert ws["trace"]["nodes"], "no trace nodes"
        assert ws["patch"]["diff"], "no patch diff"
        assert ws["changed_files"], "no changed files"
        assert ws["validation"]["gates"], "no validation gates"
        assert not ws["delivery"], "delivery must not happen before approval"

        first_file = ws["changed_files"][0]["id"]
        accepted = client.post(f"{BASE}/api/runs/{run_id}/changed-files/{first_file}/accept").json()
        print("file review:", accepted)

        client.post(f"{BASE}/api/runs/{run_id}/approve").raise_for_status()
        ws = poll_until(client, run_id, lambda w: w["run"]["status"] in ("completed", "failed"))
        print("final:", ws["run"]["status"], ws["run"]["delivery_state"])
        assert ws["run"]["status"] == "completed", ws["run"]
        assert ws["delivery"]["branch"], "no delivery branch"
        assert ws["memory_update"]["status"] == "verified", ws["memory_update"]
        assert ws["changed_files"][0]["decision"] == "accepted", ws["changed_files"][0]
        assert ws["command_log"], "no commands"

        rejected_run = client.post(f"{BASE}/api/demo/run", json={"repository_url": REPO}).json()["run_id"]
        ws2 = poll_until(client, rejected_run, lambda w: w["run"]["status"] == "waiting_for_approval")
        client.post(f"{BASE}/api/runs/{rejected_run}/reject").raise_for_status()
        ws2 = client.get(f"{BASE}/api/runs/{rejected_run}/workspace").json()
        assert ws2["run"]["status"] == "rejected", ws2["run"]
        assert not ws2["delivery"], "rejected run must not deliver"
        print("reject path:", ws2["run"]["status"], "|", ws2["run"]["error"])

    print("E2E OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
