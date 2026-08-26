import urllib.request
import json
from uuid import UUID

incident_id = "c6f0888a-e33e-4b96-a9c4-8c97bab23984"
patch_id = "e03ef771-7e49-48be-aaf3-4305288880de"
url = f"http://127.0.0.1:8000/api/incidents/{incident_id}/patches/{patch_id}/deliver"

req = urllib.request.Request(url, method="POST")
try:
    response = urllib.request.urlopen(req)
    print(json.dumps(json.loads(response.read()), indent=2))
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(json.dumps(json.loads(e.read()), indent=2))
