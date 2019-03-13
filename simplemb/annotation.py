from typing import Dict
LabelDict = Dict[str,str]
ANNOTATION="__simplemb_anotation"
SUBSCRIBE = "__simplemb_subscribe"
REPLY = "__simplemb_reply"
TRIGGER = "__simplemb_trigger"
INTERFACE = "__simplemb_interface"
LABELS = "__simplemb_labels"

def on(interface: str, labels: LabelDict=None):
    def decorator(func):
        func.__simplemb_anotation = SUBSCRIBE
        func.__simplemb_interface = interface
        func.__simplemb_labels = labels
        return func
    return decorator

def reply(interface: str):
    def decorator(func):
        func.__simplemb_anotation = REPLY
        func.__simplemb_interface = interface
        return func
    return decorator

def trigger(interface: str, labels: LabelDict=None):
    def decorator(func):
        func.__simplemb_anotation = TRIGGER
        func.__simplemb_interface = interface
        func.__simplemb_labels = labels
        return func
    return decorator