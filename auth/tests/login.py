import requests

res = requests.post(
    url='http://127.0.0.1',
    data={"username": "georgio@email.com", "password": "Admin123"}
)
print(res.text)