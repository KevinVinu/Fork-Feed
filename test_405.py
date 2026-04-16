
import requests
import json

# Assuming admin token is needed, but let's just see if we get 405
url = "http://localhost:8080/Food/subfood/id/1"
data = {"foodName": "Test Item"}
headers = {"Content-Type": "application/json"}

try:
    # First test OPTIONS (Preflight)
    opt_res = requests.options(url)
    print(f"OPTIONS Status: {opt_res.status_code}")
    print(f"Allow Header: {opt_res.headers.get('Allow')}")

    # Then test PUT (will likely return 401 but not 405 if route exists)
    response = requests.put(url, json=data, headers=headers)
    print(f"PUT Status Code: {response.status_code}")
    print(f"PUT Response: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
