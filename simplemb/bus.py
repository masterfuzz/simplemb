from .signature import Signature
from .message import DebugMessage
import queue
import threading
import time
import uuid
import random

class Bus:
    def __init__(self):
        self.subscribers = {}
        self.consumer_queues = []

    def publish(self, message):
        print(f"publish {message}")
        consumed = False
        queued = False
        for mq in self.consumer_queues:
            if mq.put_if_match(message):
                consumed = True
                queued = True

        if not queued:
            print(f"no queue matched. created")
            mq = MatchQueue(Signature(message.signature.interface))
            mq.put(message)
            self.queues.append(mq)

        # observers
        for sub in self.subscribers.values():
            sub.observe(message)

        return consumed

    def subscribe(self, subscriber_id, interface=None, labels=None, observe=False):
        signature = Signature(interface, labels)
        if subscriber_id not in self.subscribers:
            print(f"new subscriber {subscriber_id}")
            self.subscribers[subscriber_id] = Subscriber()
        subscriber = self.subscribers[subscriber_id]
        if observe:
            subscriber.add_observer_signature(signature)
        else:
            subscriber.add_consumer_signature(signature)
            for mq in self.consumer_queues:
                if mq.same(signature):
                    return
            self.consumer_queues.append(MatchQueue(signature))

    def poll(self, subscriber_id, block=False):
        if subscriber_id not in self.subscribers:
            raise NoSubscriptionError()
        subscriber = self.subscribers[subscriber_id]

        for mq in self.consumer_queues:
            if subscriber.match(mq):
                try:
                    return mq.get_nowait()
                except queue.Empty:
                    continue
        
        return subscriber.get_observed()


class MatchQueue(queue.Queue):
    def __init__(self, sig, maxsize=0):
        super().__init__(maxsize)
        self.sig = sig

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
        return f"MQ({self.sig},{self.consume})"

class Subscriber:
    def __init__(self, sigs=None):
        self.sigs = sigs if sigs else []
        self.observer_queues = []

    def add_consumer_signature(self, signature):
        self.sigs.append(signature)

    def add_observer_signature(self, signature):
        self.observer_queues.append(MatchQueue(signature))
    
    def match(self, mq):
        return any(mq.sig.match(sig) for sig in self.sigs)

    def observe(self, msg):
        for mq in self.observer_queues:
            if mq.put_if_match(msg):
                return
    
    def get_observed(self):
        for mq in self.observer_queues:
            try:
                return mq.get_nowait()
            except queue.Empty:
                continue
        raise queue.Empty()


class NoSubscriptionError(Exception):
    pass