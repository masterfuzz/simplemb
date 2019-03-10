from .agent import Agent
import time

class BusCtlAgent(Agent):
    def __init__(self, bus):
        super().__init__(bus, name="BUSCTL")
        self.reply('BUSCTL.*')(self.command)
    
    def command(self, msg):
        try:
            cmd = getattr(self, msg.signature.interface[-1])
        except AttributeError:
            return None # todo "reply" needs to handle exceptions better
        return cmd(msg)

    def get_subscribers(self, msg):
        now = time.time()
        return list({
            "uuid": s.uuid,
            "name": s.name,
            "created": s.created,
            "updated": s.updated,
            "stale_time": now - s.polled
        } for s in self.bus.subscribers.values())

    def get_queues(self, msg):
        return [str(mq.sig) for mq in self.bus.consumer_queues]

    def get_tree(self, msg):
        tree = {}
        for q in self.bus.consumer_queues:
            _add_to_tree(tree, q.sig.interface, q.sig.labels)
        return tree
            
def _add_to_tree(tree, interface, labels):
    if len(interface) == 0:
        tree['leaves'] = tree.get('leaves', []) + [labels]
        return
    rt = interface[0]
    if rt not in tree:
        tree[rt] = {}
    _add_to_tree(tree[rt], interface[1:], labels)
