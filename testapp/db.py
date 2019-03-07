from simplemb.rest import RestAgent

agent = RestAgent("http://localhost:8000/", name="db")
# validator = RestAgent("http://localhost:8000/", name="db.validator")
agent.start()

data = {
    "hello": "world",
    "other": "things"
}

@agent.reply("db.get.*")
def get(msg):
    # validate token
    print(f"got request {msg}")
    token = msg.signature.labels.get('token')
    if not token:
        print("malformed request")
        return None

    req = agent.request("Auth.Validate", payload=token)
    print(f"made request to validate token {req}")
    res = req.join()

    if not res.payload:
        print(f"auth responded with invalid token {res}")
        return None
    field = msg.signature.interface[-1]
    if field:
        print(f"returning data.get({field})=={data.get(field)}")
        return data.get(field)
    else:
        print(f"not sure how you didn't have a field")

