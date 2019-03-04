import simplequeue
import restagent
import time

bus = restagent.RestBusClient("http://localhost:8000/")
logger = simplequeue.Agent(bus)

agentpool = simplequeue.AgentPool(lambda n: simplequeue.Agent(bus, {'n': str(n)}), count=5)
for a in agentpool.pool:
    a.subscribe("Kill", func=a.stop(), labels={"agentUUID": a.uuid})


@logger.sub("", consume=False)
def log(msg):
    if msg.signature.labels:
        labels = ", ".join(f"{k}={v}" for k,v in msg.signature.labels.items())
        print(f"{msg.source[:8]} {'.'.join(msg.signature.interface)}({labels}): {msg.payload}")
    else:
        print(f"{msg.source[:8]} {'.'.join(msg.signature.interface)}(): {msg.payload}")

logger.start()
agentpool.start()

time.sleep(2)
for a in agentpool.pool:
    logger.publish("Kill", labels={"agentUUID": a.uuid})

agentpool.join()
logger.stop()
logger.join()
