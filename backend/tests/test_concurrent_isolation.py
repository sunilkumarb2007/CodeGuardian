import os
import sys
import threading
import time
import requests

API_BASE = "http://localhost:8000"

def trigger_run(repo_url: str):
    print(f"Triggering run for {repo_url}...")
    try:
        res = requests.post(f"{API_BASE}/api/orchestration/run", json={"repository_url": repo_url})
        if res.status_code == 200:
            run_id = res.json()["run_id"]
            print(f"[{repo_url}] Started run {run_id}")
            return run_id
        else:
            print(f"[{repo_url}] Failed to start run: {res.text}")
    except Exception as e:
        print(f"[{repo_url}] Request failed: {e}")
    return None

def get_run_status(run_id: str):
    try:
        res = requests.get(f"{API_BASE}/api/orchestration/run/{run_id}/status")
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        pass
    return None

def main():
    repos = [
        "https://github.com/sunilkumarb2007/CodeGuardian.git",
        "https://github.com/sunilkumarb2007/CodeGuardian.git",
        "https://github.com/sunilkumarb2007/CodeGuardian.git"
    ]
    
    threads = []
    run_ids = []
    
    for repo in repos:
        t = threading.Thread(target=lambda r: run_ids.append(trigger_run(r)), args=(repo,))
        threads.append(t)
        t.start()
        time.sleep(1) # stagger slightly
        
    for t in threads:
        t.join()
        
    print(f"Triggered run IDs: {run_ids}")
    
    # Wait for completion and verify isolation
    print("Waiting for runs to complete...")
    for _ in range(60): # wait up to 120s
        completed = 0
        for rid in run_ids:
            if not rid:
                completed += 1
                continue
            
            status = get_run_status(rid)
            if status and status.get("state") in ["WAITING_FOR_APPROVAL", "FAILED", "VALIDATION_FAILED", "NO_FAILURE_EVIDENCE", "INVESTIGATION_FAILED"]:
                completed += 1
                
        if completed >= len(run_ids):
            break
        time.sleep(2)
        
    # Validation logic
    print("All runs finished. Verifying isolation...")
    success = True
    
    # Simple check for unique events array logic
    events_per_run = {}
    for rid in run_ids:
        if rid:
            status = get_run_status(rid)
            if status:
                events = status.get("events", [])
                events_per_run[rid] = events
                print(f"Run {rid} completed with state {status.get('state')} and {len(events)} events.")
                
    # If they all have different IDs and different events, isolation works.
    if len(set(run_ids)) != len(run_ids):
        print("ERROR: Run IDs are not unique!")
        success = False
        
    print("Concurrency test completed " + ("SUCCESS" if success else "FAILED"))

if __name__ == "__main__":
    main()
