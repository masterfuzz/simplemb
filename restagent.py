import simplequeue
import requests
import queue
import time

class RestBusClient:
    def __init__(self, url):
        self.url = url
        self.ses = requests.Session()
        self.retry = 1.0

    def publish(self, message, retry_no_sub=False):
        req = requests.Request('PUT',
                self.url + 'pub/' + '.'.join(message.signature.interface),
                json={'labels': message.signature.labels,
                      'payload': message.payload,
                      'source': str(message.source)}).prepare()
        while True:
            try:
                res = self.ses.send(req)
                if res.ok:
                    return True
                elif retry_no_sub:
                    print("no subscribers available. retrying...")
                else:
                    return False
            except:
                print("exception communicating with the bus. Retrying...")
            time.sleep(self.retry)

    def subscribe(self, subscriber_id, interface=None, labels=None, consume=True):
        req = requests.Request('PUT',
                self.url + "sub/" + str(subscriber_id),
                json={'labels': labels,
                      'interface': interface,
                      'consume': consume}).prepare()
        while True:
            try:
                res = self.ses.send(req)
                return
            except:
                print("exception communicating with the bus. retry")
            time.sleep(self.retry)

    def poll(self, subscriber_id, block=True):
        try:
            res = requests.get(self.url + f"poll/{subscriber_id}")
            if res.ok:
                return simplequeue.Message.from_dict(res.json())
            else:
                raise queue.Empty()
        except queue.Empty:
            raise queue.Empty()
        except Exception as e:
            print("exception communicating with the bus")
            raise queue.Empty() from e

class RestAgent(simplequeue.Agent):
    def __init__(self, url, labels=None, name=None):
        super().__init__(RestBusClient(url), labels=labels, name=name)
