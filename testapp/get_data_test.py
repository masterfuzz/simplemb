from simplemb.rest.restagent import RestAgent
from simplemb.agent import RemoteAgent

agent = RestAgent("http://localhost:8000/", name="client")
auth = RemoteAgent(agent, "Auth")
data = RemoteAgent(agent, "db")
agent.start()

def login():
    # req = agent.request("Auth.Login", payload="bob/bob")
    req = auth.Login.request("bob/bob")
    print(f"Made login request f{req.request_id}")
    result = req.join()
    if result.payload:
        return result.payload
    else:
        print("login failed")
        agent.stop()
        raise Exception

def do_stuff(token):
    # print("hello " + agent.request("db.get.hello", labels={'token': token}).join().payload)
    req = data.get.hello.request()
    print(f"hello: {req.join().payload}")
    req = data.get.this.request()
    print(f"this.is: {req.join().payload['is']}")


token = login()
do_stuff(token)

agent.stop()

