import restagent

agent = restagent.RestAgent("http://localhost:8000/", name="client")

# my state
token = None
data = None

def login_result(msg):
    if msg.payload:
        token = msg.payload
    else:
        print("login failed")
        agent.stop()
        return
    print("do some things...")
    agent.stop()



request_id = agent.request("Auth.Login", payload="bob/bob", callback=login_result)

print(f"Made login request f{request_id}")

agent.start()

agent.join()