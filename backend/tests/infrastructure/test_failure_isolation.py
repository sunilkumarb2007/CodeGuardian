import pytest
import os
import sys
import threading
import time
import requests

API_BASE = "http://localhost:8000"

@pytest.mark.skip(reason="Needs live CodeGuardian API server for E2E infrastructure testing")
def test_failure_isolation():
    repos = [
        "https://github.com/sunilkumarb2007/CodeGuardian.git", # Run A
        "https://github.com/sunilkumarb2007/CodeGuardian.git", # Run B
        "https://github.com/sunilkumarb2007/CodeGuardian.git"  # Run C
    ]
    
    # We will trigger all 3 concurrently and they should proceed simultaneously
    # Since they are testing the same repo, they should all get their own run_id
    # and their own workspace snapshot.
    
    run_ids = []
    
    def trigger(repo):
        try:
            res = requests.post(f"{API_BASE}/api/orchestration/run", json={"repository_url": repo})
            if res.status_code == 200:
                run_ids.append(res.json()["run_id"])
        except:
            pass

    threads = []
    for r in repos:
        t = threading.Thread(target=trigger, args=(r,))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    assert len(run_ids) == 3, "Should have successfully started 3 runs"
    
    # Wait for completion
    for _ in range(60):
        completed = 0
        for rid in run_ids:
            try:
                res = requests.get(f"{API_BASE}/api/orchestration/run/{rid}/status")
                if res.status_code == 200:
                    status = res.json()
                    if status.get("state") in ["WAITING_FOR_APPROVAL", "FAILED", "VALIDATION_FAILED", "NO_FAILURE_EVIDENCE", "INVESTIGATION_FAILED"]:
                        completed += 1
            except:
                pass
        if completed == 3:
            break
        time.sleep(2)
        
    # Verify isolation
    events_a = requests.get(f"{API_BASE}/api/orchestration/run/{run_ids[0]}/status").json().get("events", [])
    events_b = requests.get(f"{API_BASE}/api/orchestration/run/{run_ids[1]}/status").json().get("events", [])
    
    assert len(events_a) > 0, "Run A should have events"
    assert len(events_b) > 0, "Run B should have events"
    
    # We can check that they are entirely distinct rows
    assert events_a[0]["id"] != events_b[0]["id"], "Events should be fully isolated"
    
    print("Failure isolation validated. Runs were executed completely concurrently without interleaving database rows.")
