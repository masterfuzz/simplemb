import uuid

class Signature:
    def __init__(self, interface, labels=None):
        self.labels = labels.copy() if labels else {}
        self.interface = interface.split('.') if interface else []
        self.uuid = str(uuid.uuid1())

    def match(self, sig):
        return (self._imatch(self.interface, sig.interface) 
                and all(sig.labels.get(k) == v for k,v in self.labels.items()))

    def _imatch(self, pat, bod):
        if pat is None or bod is None:
            return True
        if len(pat) == 0:
            if len(bod) == 0:
                return True
            else:
                return False
        if len(bod) == 0:
            return False
        if pat[0] == "**":
            return True
        if pat[0] == "*" or pat[0] == bod[0]:
            return self._imatch(pat[1:], bod[1:])
        else:
            return False

    def __repr__(self):
        return f"SIG[{'.'.join(self.interface)}]{self.labels}"

    def __str__(self):
        labels = ", ".join(f"{k}={v}" for k,v in self.labels.items())
        return f"{'.'.join(self.interface)}({labels})"