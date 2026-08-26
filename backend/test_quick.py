import httpx
base_url = 'http://127.0.0.1:8000'
r = httpx.get(f'{base_url}/api/incidents')
for inc in r.json():
    print(f"Incident {inc['id']}")
    print('Trace:', httpx.get(f"{base_url}/api/incidents/{inc['id']}/trace").status_code)
    print('Memory:', httpx.get(f"{base_url}/api/incidents/{inc['id']}/memory").status_code)
