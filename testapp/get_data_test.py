from simplemb.rest.restagent import RestAgent

agent = RestAgent("http://localhost:8000/", name="client")
agent.start()

def login():
    req = agent.request("Auth.Login", payload="bob/bob")
    print(f"Made login request f{req.request_id}")
    result = req.join()
    if result.payload:
        return result.payload
    else:
        print("login failed")
        agent.stop()
        raise Exception

def do_stuff(token):
    print(agent.request("db.get.hello", labels={'token': token}).join())


token = login()
do_stuff(token)

agent.stop()

