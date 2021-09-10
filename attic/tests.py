import requests

baseUrl = "http://localhost:8080"


resp = requests.post('{0}/api/v1/model'.format(baseUrl), json={"method":"create_model","params":{"name": "stefans car"}})
data = resp.json()
print(data)


# Create model
resp = requests.post('{0}/api/v1/model'.format(baseUrl), json={"method":"create_model"})
data = resp.json()
print(data)

name = data['data']['model']['name']

# Create model with same name. This should issue an error
resp = requests.post('{0}/api/v1/model'.format(baseUrl), json={"method":"create_model", "params": {"name": name}})
print(resp.json())

# Fetch the model by name
resp = requests.get('{0}/api/v1/model/{1}'.format(baseUrl, name))
print(resp.json())

# Update model
resp = requests.put('{0}/api/v1/model/{1}'.format(baseUrl, name), params={"make":"subaru"}, json={"method":"update_model", "params": {"color":"blue"}})
print(resp.json())

# Check if model got updated
resp = requests.get('{0}/api/v1/model/{1}'.format(baseUrl, name))
print(resp.json())

# Create model
resp = requests.post('{0}/api/v1/model'.format(baseUrl), json={"method":"create_model"})
data = resp.json()
print(data)

name = data['data']['model']['name']

# Delete model
resp = requests.delete('{0}/api/v1/model/{1}'.format(baseUrl, name))
print(resp.json())

# Get deleted model
resp = requests.get('{0}/api/v1/model/{1}'.format(baseUrl, name))
print(resp.json())
