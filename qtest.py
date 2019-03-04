import simplequeue
import restagent
import time

bus = restagent.RestBusClient("http://localhost:8000/")
agentA = simplequeue.Agent(bus)
agentB = simplequeue.Agent(bus)
agentC = simplequeue.Agent(bus)

@agentA.subscribe("Hello")
def respond(msg):
    agentA.publish("Log", msg.payload)

@agentA.subscribe("TimesTwo")
def times_two(msg):
    agentA.publish("Log", msg.payload * 2)

@agentC.subscribe("TimesTwo")
def times_two(msg):
    agentC.publish("Log", msg.payload * 2.1)

@agentA.subscribe("Kill", labels={"agentUUID": agentA.uuid})
def endAgentA(msg):
    agentA.publish("Log", f"agent A exiting at request of {msg.source}")
    agentA.live = False

@agentB.subscribe("Kill", labels={"agentUUID": agentB.uuid})
def endAgentB(msg):
    print("logging service killed")
    agentB.live = False

@agentC.subscribe("Kill", labels={"agentUUID": agentC.uuid})
def endAgentC(msg):
    agentC.live = False

@agentB.subscribe("", consume=False)
def log(msg):
    if msg.signature.labels:
        labels = ", ".join(f"{k}={v}" for k,v in msg.signature.labels.items())
        print(f"{msg.source} {'.'.join(msg.signature.interface)}({labels}): {msg.payload}")
    else:
        print(f"{msg.source} {'.'.join(msg.signature.interface)}(): {msg.payload}")

for x in range(5):
    agentB.publish("TimesTwo", x)

agentA.start()
agentB.start()
agentC.start()

agentB.publish("Hello", "Hello")
agentB.publish("Hello", "World")
agentB.publish("TimesTwo", 5)
agentB.publish("TimesTwo", 50)

time.sleep(2)
agentB.publish("Kill", labels={"agentUUID": agentA.uuid})
agentB.publish("Kill", labels={"agentUUID": agentC.uuid})
time.sleep(2)
agentB.publish("Kill", labels={"agentUUID": agentB.uuid})
