from typing import Dict
from .annotation_constants import SUBSCRIBE, REPLY, TRIGGER
__LabelDict = Dict[str,str]

def on(interface: str=None, labels: __LabelDict=None):
    def decorator(func):
        func.__simplemb_anotation = SUBSCRIBE
        func.__simplemb_interface = interface
        func.__simplemb_labels = labels
        return func
    return decorator

def reply(interface: str=None):
    def decorator(func):
        func.__simplemb_anotation = REPLY
        func.__simplemb_interface = interface
        return func
    return decorator

def trigger(interface: str=None, labels: __LabelDict=None):
    def decorator(func):
        func.__simplemb_anotation = TRIGGER
        func.__simplemb_interface = interface
        func.__simplemb_labels = labels
        return func
    return decorator