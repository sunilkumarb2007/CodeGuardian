import urllib.request
import json
import time

url = "http://127.0.0.1:8000/api/orchestration/run"
data = json.dumps({"repository_url": "https://github.com/sunilkumarb2007/JavaAPICheck"}).encode("utf-8")
headers = {"Content-Type": "application/json"}

req = urllib.request.Request(url, data=data, headers=headers, method="POST")
try:
    response = urllib.request.urlopen(req)
    result = json.loads(response.read())
    run_id = result["run_id"]
    print(f"Run started: {run_id}")
    
    while True:
        time.sleep(2)
        status_req = urllib.request.Request(f"http://127.0.0.1:8000/api/orchestration/runs/{run_id}")
        status_resp = urllib.request.urlopen(status_req)
        status_data = json.loads(status_resp.read())
        
        print(f"Status: {status_data['status']}, Stage: {status_data['current_stage']}")
        if status_data["status"] in ["completed", "failed", "completed_no_action"]:
            result_req = urllib.request.Request(f"http://127.0.0.1:8000/api/orchestration/runs/{run_id}/result")
            result_resp = urllib.request.urlopen(result_req)
            result_data = json.loads(result_resp.read())
            print(json.dumps(result_data, indent=2))
            break
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(json.dumps(json.loads(e.read()), indent=2))
except Exception as e:
    print(f"Error: {e}")

