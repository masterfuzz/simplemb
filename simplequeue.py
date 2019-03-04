import queue
import threading
import time
import uuid

class Bus:
    def __init__(self):
        self.queues = {}

    def publish(self, message):
        for q in self.queues.values():
            if q.put_if_match(message) and q.consume:
                return

    def subscribe(self, subscriber_id, interface=None, labels=None, consume=True):
        sig = Signature(interface,labels)
        if subscriber_id not in self.queues:
            self.queues[subscriber_id] = SubscriberQueue([sig], consume=consume)
            # print(f"{subscriber_id} [NEW] subscribed to {sig}")
        else:
            self.queues[subscriber_id].append(sig)
            # print(f"{subscriber_id} subscribed to {sig}")

    def poll(self, subscriber_id, block=True):
        if subscriber_id in self.queues:
            return self.queues[subscriber_id].get(block=block)

class Signature:
    def __init__(self, interface, labels=None):
        self.labels = labels if labels else {}
        self.interface = interface.split('.') if interface else []
        self.uuid = str(uuid.uuid1())

    def match(self, sig):
        # A match A
        # A.B match A
        # A.B.C match A.B
        interface_match = True
        if self.interface is None or len(self.interface) == 0:
            interface_match = True
        elif len(sig.interface) < len(self.interface):
            interface_match = False
        else:
            for i in range(len(self.interface)):
                if self.interface[i] != sig.interface[i]:
                    interface_match = False
                    break
        return interface_match and all(sig.labels.get(k) == v for k,v in self.labels.items())

    def __repr__(self):
        return f"SIG[{'.'.join(self.interface)}]{self.labels}"

class SubscriberQueue(queue.Queue):
    def __init__(self, sigs=None, consume=True, maxsize=0):
        super().__init__(maxsize)
        self.sigs = sigs if sigs else []
        self.consume = True if consume else False

    def put_if_match(self, message):
        if any(sig.match(message.signature) for sig in self.sigs):
            # print(f"{self} holding {message}")
            self.put(message)
            return True
        else:
            # print(f"{self} rejected {message}")
            return False

    def append(self, sig):
        self.sigs.append(sig)

    def __repr__(self):
        return f"<SQ({len(self.sigs)},{self.consume})>"


class Message:
    def __init__(self, payload, signature, source=None):
        self.signature = signature
        self.payload = payload
        self.source = source

    def __repr__(self):
        return f"<msg({self.signature})>"

    @classmethod
    def from_dict(cls, data):
        return cls(data.get("payload"),
                        Signature(data.get("interface"), data.get("labels")),
                        source=data.get("source"))

    def to_dict(self):
        return {"interface": ".".join(self.signature.interface),
                "payload": self.payload,
                "labels": self.signature.labels,
                "source": self.source}


class Agent(threading.Thread):
    def __init__(self, bus):
        super().__init__()
        self.bus = bus
        self.uuid = str(uuid.uuid1())
        self.sigs = []
        self.live = True
        self.max_backoff = 1.0
        self.min_sleep = 0.1
        self.cur_sleep = self.min_sleep

    def run(self):
        self.publish("Log", "Begin polling")
        while self.live:
            try:
                msg = self.bus.poll(self.uuid)
                if msg:
                    for sig, callback in self.sigs:
                        if sig.match(msg.signature):
                            callback(msg)
                    self.cur_sleep = self.min_sleep
                else:
                    self.sleep()
            except queue.Empty:
                self.sleep()

    def sleep(self):
        time.sleep(self.cur_sleep)
        self.cur_sleep = max(self.max_backoff, self.cur_sleep*2)

    def subscribe(self, interface, labels=None, consume=True):
        def decorator(func):
            def wrap(*args, **kwargs):
                return func(*args, **kwargs)
            sig = Signature(interface, labels)
            self.sigs.append((sig, func))
            self.bus.subscribe(self.uuid, interface, labels, consume)
            return wrap
        return decorator

    def publish(self, interface, payload=None, labels=None):
        self.bus.publish(Message(payload=payload, signature=Signature(interface, labels), source=self.uuid))


