from .signature import Signature
from .message import DebugMessage
import logging
import queue
import threading
import time
import uuid
import random

log = logging.getLogger("bus")
log.addHandler(logging.NullHandler())


class Bus:
    def __init__(self):
        self.subscribers = {}
        self.consumer_queues = []

    def publish(self, message):
        log.debug(f"publish {message}")
        consumed = False
        queued = False
        for mq in self.consumer_queues:
            if mq.put_if_match(message):
                log.info(f"publish {message} to {mq}")
                consumed = True
                queued = True

        if not queued:
            log.info(f"publish {message} to new consumer queue")
            mq = MatchQueue(Signature(message.signature.interface))
            mq.put(message)
            self.consumer_queues.append(mq)

        # observers
        for key, sub in self.subscribers.items():
            if sub.observe(message):
                log.info(f"published {message} to observer {key}")

        return consumed

    def subscribe(self, subscriber_id, interface=None, labels=None, consume=True):
        signature = Signature(interface, labels)
        if subscriber_id not in self.subscribers:
            log.info(f"new subscriber {subscriber_id}")
            self.subscribers[subscriber_id] = Subscriber(subscriber_id)
        subscriber = self.subscribers[subscriber_id]
        if not consume:
            subscriber.add_observer_signature(signature)
            log.info(f"{subscriber.uuid} observing {signature}")
        else:
            subscriber.add_consumer_signature(signature)
            for mq in self.consumer_queues:
                if mq.same(signature):
                    return
            self.consumer_queues.append(MatchQueue(signature))
            log.info(f"{subscriber_id} consuming {signature}")

    def poll(self, subscriber_id, block=False):
        if subscriber_id not in self.subscribers:
            raise NoSubscriptionError()
        subscriber = self.subscribers[subscriber_id]

        for mq in self.consumer_queues:
            if subscriber.match(mq):
                try:
                    res = mq.get_nowait()
                    mq.last_hit = time.time()
                    log.debug(f"send {res} to {subscriber_id}")
                    return res
                except queue.Empty:
                    continue
        
        return subscriber.get_observed()


class MatchQueue(queue.Queue):
    def __init__(self, sig, maxsize=0):
        super().__init__(maxsize)
        self.sig = sig
        self.last_hit = time.time()

    def put_if_match(self, message):
        if self.match(message):
            self.put(message)
            return True
        else:
            return False

    def match(self, message):
        return self.sig.match(message.signature)

    def same(self, sig):
        return self.sig.interface == sig.interface and self.sig.labels == sig.labels

    def __repr__(self):
        return f"MQ({self.sig})"

class Subscriber:
    def __init__(self, uuid, sigs=None, name=None):
        self.sigs = sigs if sigs else []
        self.observer_queues = []
        self.uuid = uuid
        self.name = name
        self.created = time.time()
        self.updated = self.created
        self.polled = self.created

    def add_consumer_signature(self, signature):
        self.updated = time.time()
        self.sigs.append(signature)

    def add_observer_signature(self, signature):
        self.updated = time.time()
        self.observer_queues.append(MatchQueue(signature))
    
    def match(self, mq):
        return any(mq.sig.match(sig) for sig in self.sigs)

    def observe(self, msg):
        for mq in self.observer_queues:
            if mq.put_if_match(msg):
                return True
        return False
    
    def get_observed(self):
        for mq in self.observer_queues:
            try:
                msg = mq.get_nowait()
                self.polled = time.time()
                return msg
            except queue.Empty:
                continue
        raise queue.Empty()


class NoSubscriptionError(Exception):
    pass