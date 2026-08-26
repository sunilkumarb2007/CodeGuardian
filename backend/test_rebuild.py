import httpx
import json

base_url = 'http://127.0.0.1:8000'

def test_ghosttrace():
    print("Fetching incidents...")
    r = httpx.get(f'{base_url}/api/incidents')
    incidents = r.json()
    
    for inc in incidents:
        inc_id = inc['id']
        print(f"\n--- Testing Rebuild for Incident: {inc_id} ---")
        
        rebuild_res = httpx.post(f"{base_url}/api/incidents/{inc_id}/trace/rebuild")
        print(f"Rebuild status: {rebuild_res.status_code}")
        
        if rebuild_res.status_code == 200:
            trace = rebuild_res.json()
            print(f"Symptom: {trace.get('symptom_service')}")
            print(f"Root Cause Candidate: {trace.get('root_cause_candidate')}")
            print(f"Confidence: {trace.get('confidence')}")
            print(f"Nodes: {len(trace.get('nodes', []))}")
            print(f"Edges: {len(trace.get('edges', []))}")
            
            print("\nReasoning Summary:")
            print(trace.get('reasoning_summary'))
        else:
            print(rebuild_res.text)

if __name__ == "__main__":
    test_ghosttrace()
