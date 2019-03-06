import queue
import threading
import time
import uuid
import random

class Bus:
    def __init__(self):
        self.queues = {}

    def publish(self, message):
        #super lazy scheduler for now
        subs = list(self.queues.keys())
        random.shuffle(subs)
        consumed = False
        for sub in subs:
            if consumed and self.queues[sub].consume:
                continue
            elif self.queues[sub].put_if_match(message) and self.queues[sub].consume:
                consumed = True
        return consumed

    def subscribe(self, subscriber_id, interface=None, labels=None, consume=True):
        sig = Signature(interface,labels)
        if subscriber_id not in self.queues:
            self.queues[subscriber_id] = SubscriberQueue([sig], consume=consume)
            self.publish(DebugMessage(f"{subscriber_id} [NEW] subscribed to {sig}"))
        else:
            self.queues[subscriber_id].append(sig)
            self.publish(DebugMessage(f"{subscriber_id} subscribed to {sig}"))

    def poll(self, subscriber_id, block=True):
        if subscriber_id in self.queues:
            return self.queues[subscriber_id].get(block=block)

class Signature:
    def __init__(self, interface, labels=None):
        self.labels = labels.copy() if labels else {}
        self.interface = interface.split('.') if interface else []
        self.uuid = str(uuid.uuid1())

    def match(self, sig):
        return (self._imatch(self.interface, sig.interface) 
                and all(sig.labels.get(k) == v for k,v in self.labels.items()))

    def _imatch(self, pat, bod):
        if pat is None or bod is None:
            return True
        if len(pat) == 0:
            if len(bod) == 0:
                return True
            else:
                return False
        if len(bod) == 0:
            return False
        if pat[0] == "**":
            return True
        if pat[0] == "*" or pat[0] == bod[0]:
            return self._imatch(pat[1:], bod[1:])
        else:
            return False

    def __repr__(self):
        return f"SIG[{'.'.join(self.interface)}]{self.labels}"

    def __str__(self):
        labels = ", ".join(f"{k}={v}" for k,v in self.labels.items())
        return f"{'.'.join(self.interface)}({labels})"

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
        return f"<msg({repr(self.signature)})>"
    
    def __str__(self):
        return f"{self.source}:{self.signature}<{self.payload}>"

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

class DebugMessage(Message):
    def __init__(self, msg):
        super().__init__(msg, Signature("DEBUG"), source="ROOT")

class Agent(threading.Thread):
    def __init__(self, bus, labels=None, name=None):
        super().__init__()
        self.bus = bus
        self.uuid = str(uuid.uuid1())
        self.sigs = []
        self.live = True
        self.max_backoff = 1.0
        self.min_sleep = 0.1
        self.cur_sleep = self.min_sleep
        self.labels = labels if labels else {}
        if name:
            self.set_name(name)

    def set_name(self, name):
        self.labels['name'] = name

    def _handle_agent_calls(self, msg):
        if len(msg.signature.interface) != 2:
            self.publish("Log", "Bad interface on received agent call")
            return
        func = msg.signature.interface[1].lower()
        if func == 'stop':
            self.stop()
        else:
            self.publish("Log", f"Unknown interface {func} received on agent call")

    def run(self):
        self.publish("Log", "Begin polling")
        self.subscribe("Agent.**", func=self._handle_agent_calls, labels={'agentUUID': self.uuid})
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

    def stop(self):
        self.live = False
        # self.join()

    def sleep(self):
        time.sleep(self.cur_sleep)
        self.cur_sleep = min(self.max_backoff, self.cur_sleep*2)

    def subscribe(self, interface, func, labels=None, consume=True):
        sig = Signature(interface, labels)
        self.sigs.append((sig, func))
        self.bus.subscribe(self.uuid, interface, labels, consume)
        

    def sub(self, interface, labels=None, consume=True):
        def decorator(func):
            def wrap(*args, **kwargs):
                return func(*args, **kwargs)
            self.subscribe(interface, func, labels, consume)
            return wrap
        return decorator

    def reply(self, interface):
        def decorator(func):
            def wrap(msg):
                print(f"reply wrap function called on {msg}")
                self.publish(interface+'.Result',
                     func(msg),
                     labels={'reqID': msg.signature.labels['reqID']}
                    )
            print(f"reply inner decorator called on {func}")
            self.subscribe(interface, wrap)
            return wrap
        print(f"reply outer decorator called for {interface}")
        return decorator

    def request(self, interface, callback, payload=None):
        reqID = str(uuid.uuid4())
        self.subscribe(interface+'.Result', callback, labels={'reqID': reqID})
        self.publish(interface, payload, {'reqID': reqID})
        return reqID

    def publish(self, interface, payload=None, labels=None):
        if labels:
            labels.update(self.labels)
        else:
            labels = self.labels
        return self.bus.publish(Message(payload=payload, signature=Signature(interface, labels), source=self.uuid))


class AgentPool:
    def __init__(self, init_func, count, labels=None):
        self.pool = [init_func(i) for i in range(count)]
        if labels:
            for a in self.pool:
                a.labels.update(labels)
    
    def start(self):
        for a in self.pool:
            a.start()

    def stop(self):
        for a in self.pool:
            a.stop()
            a.join()

    def join(self):
        for a in self.pool:
            a.join()


    