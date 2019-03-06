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
