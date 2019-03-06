from .signature import Signature

class Message:
    def __init__(self, payload, signature, source=None):
        self.signature = signature
        self.payload = payload
        self.source = source

    def __repr__(self):
        return f"<msg({repr(self.signature)})>"
    
    def __str__(self):
        return f"{self.source}:{self.signature}<{self.payload}>"

    @classmethod
    def from_dict(cls, data):
        return cls(data.get("payload"),
                        Signature(data.get("interface"), data.get("labels")),
                        source=data.get("source"))

    def to_dict(self):
        return {"interface": ".".join(self.signature.interface),
                "payload": self.payload,
                "labels": self.signature.labels,
                "source": self.source}

class DebugMessage(Message):
    def __init__(self, msg):
        super().__init__(msg, Signature("DEBUG"), source="ROOT")
