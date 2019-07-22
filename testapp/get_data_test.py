from simplemb.rest.restagent import RestAgent

agent = RestAgent("http://localhost:8000/", name="client")
auth = agent.get_remote("Auth")
data = agent.get_remote("db")
agent.start()

def login():
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

