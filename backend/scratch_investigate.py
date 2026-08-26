import urllib.request
import json

incident_id = "c6f0888a-e33e-4b96-a9c4-8c97bab23984"
url = f"http://127.0.0.1:8000/api/incidents/{incident_id}/investigate"

req = urllib.request.Request(url, method="POST")
try:
    response = urllib.request.urlopen(req)
    data = json.loads(response.read())
    print("SUCCESS")
    print(json.dumps(data, indent=2))
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(json.dumps(json.loads(e.read()), indent=2))
