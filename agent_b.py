import restagent
import time

agent = restagent.RestAgent("http://localhost:8000/")

x = 0
while True:
    if not agent.publish("TestQueue", f"Hello World! {x}"):
        print("no subscribers")
        time.sleep(1.0)
        continue
    x += 1
    time.sleep(0.2)
