import requests

url = "http://127.0.0.1:30808/login"

payload = {'username': 'georgio@email.com',
           'password': 'Admin123'}
files = [

]
headers = {}

response = requests.request("POST", url, headers=headers, data=payload, files=files)

print(response.text)
