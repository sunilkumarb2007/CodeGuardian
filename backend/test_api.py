import httpx
import sys

def run_tests():
    base_url = "http://127.0.0.1:8000"
    
    # 1. Test Health
    r = httpx.get(f"{base_url}/health")
    print(f"Health: {r.status_code} - {r.json()}")
    
    # 2. Test DB Health
    r = httpx.get(f"{base_url}/health/database")
    print(f"DB Health: {r.status_code} - {r.json()}")
    
    # 3. Test Incidents List
    r = httpx.get(f"{base_url}/api/incidents")
    print(f"Incidents List: {r.status_code}")
    incidents = r.json()
    print(f"Found {len(incidents)} incidents")
    
    if not incidents:
        print("No incidents found, exiting.")
        return
        
    incident_id = incidents[0]['id']
    print(f"\nTesting with incident_id: {incident_id}")
    
    # 4. Test Incident Detail
    r = httpx.get(f"{base_url}/api/incidents/{incident_id}")
    print(f"Incident Detail: {r.status_code}")
    
    # 5. Test Evidence
    r = httpx.get(f"{base_url}/api/incidents/{incident_id}/evidence")
    print(f"Evidence: {r.status_code} - Count: {len(r.json())}")
    
    # 6. Test Trace
    r = httpx.get(f"{base_url}/api/incidents/{incident_id}/trace")
    print(f"Trace: {r.status_code}")
    
    # 7. Test Memory
    r = httpx.get(f"{base_url}/api/incidents/{incident_id}/memory")
    print(f"Memory: {r.status_code}")

if __name__ == "__main__":
    run_tests()
