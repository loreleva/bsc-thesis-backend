import requests, json
r = requests.get("http://127.0.0.1:5000/cases")
pretty_json = json.loads(r.text)
print (json.dumps(pretty_json, indent=2))


