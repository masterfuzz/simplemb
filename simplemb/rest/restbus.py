import queue
from bottle import run, get, put, request, abort
from ..bus import Bus, NoSubscriptionError
from ..message import Message
from ..busctl import BusCtlAgent

bus = Bus()
busctl = BusCtlAgent(bus)
busctl.start()

@get('/poll/<sub_id>')
def poll(sub_id):
    try:
        res = bus.poll(sub_id, block=False)
        if res:
            return res.to_dict()
        else:
            abort(code=500)
    except NoSubscriptionError:
        abort(code=404)
    except queue.Empty:
        abort(code=304)

@put('/pub/<interface>')
def publish(interface):
    message_dict = dict(request.json)
    message_dict['interface'] = interface
    msg = Message.from_dict(message_dict)
    print(f"publish {msg}")
    if not bus.publish(msg):
        print("failed")
        abort()

@put('/sub/<sub_id>')
def subscribe(sub_id):
    signature_dict = dict(request.json)
    bus.subscribe(sub_id, signature_dict.get("interface"), 
        signature_dict.get("labels"), signature_dict.get("consume"))

def main(host='localhost', port=8000):
    run(host=host, port=port)


if __name__ == "__main__":
    main()