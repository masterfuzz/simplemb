import simplequeue
import requests
import queue

class RestBusClient:
    def __init__(self, url):
        self.url = url

    def publish(self, message):
        requests.put(self.url + 'pub/' + '.'.join(message.signature.interface),
                        json={'labels': message.signature.labels,
                                'payload': message.payload,
                                'source': str(message.source)})

    def subscribe(self, subscriber_id, interface=None, labels=None, consume=True):
        requests.put(self.url + "sub/" + str(subscriber_id),
                        json={'labels': labels, 'interface': interface, 'consume': consume})

    def poll(self, subscriber_id, block=True):
        res = requests.get(self.url + f"poll/{subscriber_id}")
        if res.ok:
            return simplequeue.Message.from_dict(res.json())
        else:
            raise queue.Empty

class RestAgent(simplequeue.Agent):
    def __init__(self, url):
        super().__init__(RestBusClient(url))
