from .signature import Signature
from .message import Message
from .bus import NoSubscriptionError
import queue
import threading
import uuid
import time

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
            except NoSubscriptionError:
                print("NoSubscription!")
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
                self.publish(msg.signature.interface+['Result'],
                     func(msg),
                     labels={'reqID': msg.signature.labels['reqID']}
                    )
            print(f"reply inner decorator called on {func}")
            self.subscribe(interface, wrap)
            return wrap
        print(f"reply outer decorator called for {interface}")
        return decorator

    def request(self, interface, callback=None, payload=None, labels=None):
        req = Request(callback=callback)
        labels = labels if labels else {}
        labels['reqID'] = req.request_id
        self.subscribe(interface+'.Result', req.set_result, labels={'reqID': req.request_id})
        self.publish(interface, payload, labels=labels)
        return req

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

class Request:
    def __init__(self, callback=None, request_id=None):
        self.request_id = request_id if request_id else str(uuid.uuid4())
        self.result = None
        self.ready = False
        self.callback = callback

    def set_result(self, result):
        self.result = result
        self.ready = True
        if self.callback:
            self.callback(result)

    def set_callback(self, callback):
        self.callback = callback

    def join(self):
        while True:
            if self.ready:
                return self.result
            print("request not received. waiting")
            time.sleep(0.1)

    def __str__(self):
        return f"Request({self.request_id})"
