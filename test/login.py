import requests

url = "http://mp3converter.com/login"

payload = {'username': 'georgio@email.com',
           'password': 'Admin123'}
files = [

]
headers = {}

response = requests.request("POST", url, headers=headers, data=payload, files=files)

print(response.text)
