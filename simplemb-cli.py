import simplemb.rest
import json
import sys

ra = simplemb.rest.RestAgent("http://localhost:8000/", name="CLI")
ra.start()

interface = sys.argv[1]
labels = {k: v for k,v in map(lambda a: a.split('=',1), sys.argv[2:])}

req = ra.request(interface, labels=labels)
print(f"Request made {req.request_id}...")
resp = req.join()
print(f"Response from {resp.source}:")
if resp.signature.labels:
    print("\n".join(f"{k}={v}" for k,v in resp.signature.labels.items()))
    print()
print(json.dumps(resp.payload, indent=2))

ra.stop()