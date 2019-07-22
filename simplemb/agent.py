from .signature import Signature
from .message import Message
from .bus import NoSubscriptionError, Bus
from .annotation_constants import *
from typing import Callable, Dict
import logging
import queue
import threading
import uuid
import time

log = logging.getLogger("agent")
log.addHandler(logging.NullHandler())

LabelDict = Dict[str, str]


class Agent(threading.Thread):
    def __init__(self, bus: Bus, labels: LabelDict=None, name=""):
        super().__init__()
        self.bus = bus
        self.uuid = str(uuid.uuid1())
        self.sigs = []
        self.stopped = threading.Event()
        self.max_backoff = 0.1
        self.min_sleep = 0.01
        self.cur_sleep = self.min_sleep
        self.labels = labels if labels else {}
        self.auto_resubscribe = True
        if name:
            self.name = name
        self._process_annotated()

    def _process_annotated(self):
        for name, func in map(lambda k: (k, getattr(self, k)), dir(self)):
            if hasattr(func, ANNOTATION):
                annotation = getattr(func, ANNOTATION)
                interface = getattr(func, INTERFACE, "")
                if not interface:
                    interface = f"{self.name}.{name}"
                labels = getattr(func, LABELS, {})
                if labels is None:
                    labels = {}
                if annotation == SUBSCRIBE:
                    self.subscribe(interface, func, **labels)
                elif annotation == REPLY:
                    func = self.reply(interface)(func)
                elif annotation == TRIGGER:
                    func = self.trigger(interface, **labels)(func)
                else:
                    raise ValueError(f"Unknown annotation {annotation}")

    @property
    def name(self):
        return self.labels.get("name", self.__class__.__name__)

    @name.setter
    def name(self, name: str):
        self.labels['name'] = name

    def _handle_agent_calls(self, msg: Message):
        if len(msg.signature.interface) != 2:
            self.publish("Log", "Bad interface on received agent call")
            return
        func = msg.signature.interface[1].lower()
        if func == 'stop':
            self.stop()
        else:
            self.publish("Log", f"Unknown interface {func} received on agent call")

    def get_remote(self, name: str):
        return RemoteAgent(self, name)

    def run(self):
        self.publish("Log", "Begin polling")
        self.subscribe("Agent.**", func=self._handle_agent_calls, labels={'agentUUID': self.uuid})
        while not self.stopped.is_set():
            try:
                msg = self.bus.poll(self.uuid)
                if msg:
                    for sig, callback in self.sigs:
                        if sig.match(msg.signature):
                            self._do_callback(callback, msg)
                    self.cur_sleep = self.min_sleep
                else:
                    self.sleep()
            except queue.Empty:
                self.sleep()
            except NoSubscriptionError:
                log.error("NoSubscription!")
                if self.auto_resubscribe:
                    self.resubscribe()
                self.sleep()

    def _do_callback(self, callback: Callable, message: Message):
        thread = threading.Thread(target=callback, args=(message.payload,), kwargs=message.labels)
        thread.start()
        log.debug(f"callback thread started {thread}")

    def stop(self):
        self.stopped.set()

    def sleep(self):
        time.sleep(self.cur_sleep)
        self.cur_sleep = min(self.max_backoff, self.cur_sleep*2)

    def subscribe(self, interface: str, func: Callable, consume=True, **labels: LabelDict):
        """ Call func when a message is received with this signature """
        sig = Signature(interface, labels, consume=consume)
        self.sigs.append((sig, func))
        self._send_subscription(sig)

    def _send_subscription(self, sig: Signature):
        self.bus.subscribe(self.uuid, sig.interface, sig.labels, sig.consume)
        
    def resubscribe(self):
        """ Resubscribe all stored signatures """
        for sig, _ in self.sigs:
            self._send_subscription(sig)

    def on(self, interface: str, consume=True, **labels):
        """ Set decorated function as a callback for a received message """
        def decorator(func):
            self.subscribe(interface, func, consume, **labels)
            return func
        return decorator

    def wait(self, interface, timeout=None):
        cond = threading.Condition()
        result = None
        def callback(*args,**kwargs):
            result = (args, kwargs)
            cond.notify()
        cond.acquire()
        self.subscribe(interface, callback)
        if cond.wait(timeout):
            return result
        else:
            raise queue.Empty()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args, **kwargs):
        self.stop()

    def reply(self, interface: str):
        """ Set decorated function as a callback for a received request message """
        def decorator(func):
            def wrap(msg):
                self.publish(['RESULT'] + msg.signature.interface,
                     func(msg),
                     labels={'reqID': msg.signature.labels['reqID']}
                    )
            self.subscribe(interface, wrap)
            return wrap
        return decorator

    def request(self, interface: str, callback: Callable=None, payload=None, **labels):
        """ Send a request and subscribe callback to the reply message """
        req = Request(callback=callback)
        labels['reqID'] = req.request_id
        self.subscribe('RESULT.'+interface, req.set_result, labels={'reqID': req.request_id})
        self.publish(interface, payload, labels=labels)
        return req

    def publish(self, interface: str, payload=None, **labels):
        """ Send a message """
        if labels:
            labels.update(self.labels)
        else:
            labels = self.labels
        return self.bus.publish(Message(payload=payload, signature=Signature(interface, labels), source=self.uuid))

    def trigger(self, interface: str, **labels):
        """
        Trigger a message on interface with payload from the return value of the decorated function
        """
        def decorator(func):
            def wrap(*args, **kwargs):
                result = func(*args, **kwargs)
                self.publish(interface, payload=result, labels=labels)
                return result
            return wrap
        return decorator

    def call(self, interface=""):
        """ Build a RemoteCall """
        return RemoteCall(self, interface)

class RemoteAgent:
    def __init__(self, coagent: Agent, name: str):
        self.name = name
        self.coagent = coagent

    def _request(self, interface: str, payload=None, labels: LabelDict=None):
        return self.coagent.request(self.name + "." + interface, payload=payload, labels=labels)

    def _publish(self, interface: str, payload=None, labels: LabelDict=None):
        return self.coagent.publish(self.name + "." + interface, payload, labels)

    def __getattr__(self, attr):
        return RemoteCall(self.coagent, self.name + "." + attr)

class RemoteCall:
    def __init__(self, coagent, interface):
        self.coagent = coagent
        self.interface = interface

    def __call__(self, payload=None, **labels):
        return self.coagent.publish(self.interface, payload=payload, labels=labels)

    def as_request(self, payload=None, **labels):
        return self.coagent.request(self.interface, payload=payload, labels=labels)

    def __getattr__(self, attr):
        return RemoteCall(self.coagent, self.interface + '.' + attr)


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
    def __init__(self, callback: Callable=None, request_id: str=""):
        self.request_id = request_id if request_id else str(uuid.uuid4())
        self.result = None
        self.ready = False
        self.callback = callback

    def set_result(self, result):
        self.result = result
        self.ready = True
        if self.callback:
            self.callback(result.payload, **result.labels)

    def join(self):
        while True:
            if self.ready:
                return self.result
            time.sleep(0.1)

    def __str__(self):
        return f"Request({self.request_id})"
