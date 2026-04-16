
import requests
import json

url = "http://localhost:8080/public/login"
data = {
    "userName": "admin",
    "password": "admin123"
}
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
