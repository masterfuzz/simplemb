import restagent
import time

agent = restagent.RestAgent("http://localhost:8000/")

x = 0
while True:
    agent.publish("TestQueue", f"Hello World! {x}")
    x += 1
    time.sleep(0.2)
