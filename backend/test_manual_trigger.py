import urllib.request
import json
import sys
import time

def check_health():
    try:
        req = urllib.request.Request('http://127.0.0.1:8000/health')
        resp = urllib.request.urlopen(req, timeout=5)
        if resp.status == 200:
            return True
    except Exception:
        pass
    return False

if __name__ == '__main__':
    if not check_health():
        print("BACKEND_NOT_RUNNING")
        sys.exit(1)

    print("Backend is running. Triggering orchestration...")
    try:
        req = urllib.request.Request(
            'http://127.0.0.1:8000/api/orchestration/run',
            data=json.dumps({
                'repository_url': 'https://github.com/sunilkumarb2007/JavaAPICheck',
                'incident_id': 'd2a57169-6136-4cc7-83c6-3e21291cb14d'
            }).encode(),
            headers={'Content-Type': 'application/json'}
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read().decode())
        run_id = data['run_id']
        print(f"Triggered run: {run_id}")
        
        # Poll a small bounded number of times (e.g. 5)
        for _ in range(5):
            time.sleep(5)
            status_req = urllib.request.Request(f'http://127.0.0.1:8000/api/orchestration/runs/{run_id}')
            status_resp = urllib.request.urlopen(status_req)
            status_data = json.loads(status_resp.read().decode())
            print(f"Status: {status_data.get('status')}")
            
    except Exception as e:
        print(f"Error during trigger: {e}")
        sys.exit(1)
