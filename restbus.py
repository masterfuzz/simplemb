import simplequeue
import queue
from bottle import get, put, run, request, abort

bus = simplequeue.Bus()

@get('/poll/<sub_id>')
def poll(sub_id):
    try:
        res = bus.poll(sub_id, block=False)
        if res:
            return res.to_dict()
        else:
            abort(code=404)
    except queue.Empty:
        abort(code=404)

@put('/pub/<interface>')
def publish(interface):
    message_dict = request.json
    message_dict['interface'] = interface
    msg = simplequeue.Message.from_dict(message_dict)
    print(f"publish {msg}")
    if not bus.publish(msg):
        print("failed")
        abort()

@put('/sub/<sub_id>')
def subscribe(sub_id):
    signature_dict = request.json
    bus.subscribe(sub_id, signature_dict.get("interface"), 
        signature_dict.get("labels"), signature_dict.get("consume"))



run(host='localhost', port=8000)