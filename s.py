import requests
import hashlib
from private_info import *

url = "https://securepay.tinkoff.ru/v2/Init"

headers = {'Content-Type': 'application/json'}


r = {
    "TerminalKey": tinkoff_terminalkey,
    "Amount": 1000,
    "OrderId": "1",
    "Password": tinkoff_password
}

t = []

for key, value in r.items():
    if key == "TerminalKey" or key == "Amount" or key == "OrderId" or key == "Password":
        t.append({key: value})
t = sorted(t, key=lambda x: list(x.keys())[0])
t = "".join(str(value) for item in t for value in item.values())
sha256 = hashlib.sha256()
sha256.update(t.encode('utf-8'))
t = sha256.hexdigest()
r["Token"] = t
print(r)
response = requests.post(url, headers=headers, json=r)
print(response)
print(response.json())
print(response.json()['PaymentURL'])