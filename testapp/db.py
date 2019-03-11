from simplemb.rest import RestAgent
import json

with open("db.json") as fp:
    data = json.load(fp)

agent = RestAgent("http://localhost:8000/", name="db")
agent.start()

@agent.reply("db.get.*")
def get(msg):
    print(f"got request {msg}")
    def _get(tree, path):
        if len(path) == 1:
            return tree[path[0]]
        else:
            return _get(tree[path[0]], path[1:]) 
    return _get(data, msg.signature.interface[2:])

@agent.sub("db.set.**")
def set_key(msg):
    def _set(tree, path, val):
        if len(path) == 1:
            tree[path[0]] = val
        else:
            if path[0] not in tree:
                tree[path[0]] = {}
            _set(tree[path[0]], path[1:], val)
        
    _set(data, msg.signature.interface[2:], msg.payload)

@agent.sub("db.save")
def write_data(msg):
    with open("db.json") as fp:
        json.dump(data, fp)

