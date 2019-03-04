import restagent

agent = restagent.RestAgent("http://localhost:8000/")

@agent.sub("TestQueue")
def respond(msg):
    print(f"i got the message: {msg.payload}")

agent.start()
agent.join()