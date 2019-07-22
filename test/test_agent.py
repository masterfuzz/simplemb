import unittest
from simplemb.agent import Agent
from simplemb.bus import Bus
import logging
logging.basicConfig(filename='testing.log',level=logging.DEBUG)

class TestAgent(unittest.TestCase):
    def setUp(self):
        self.bus = Bus()
        self.agent = Agent(self.bus, name="TestAgent", labels={"hello": "world"})

    def test_subscribe(self):
        callback = lambda *a, **k: None
        self.agent.subscribe("Test.Interface", callback)
        sig, func = self.agent.sigs[-1]
        self.assertEqual(func, callback)
        self.assertEqual(sig.interface, ["Test", "Interface"])

    def test_resubscribe(self):
        self.agent.subscribe("Test.Interface", None)
        self.agent.resubscribe()
        # ???

    def test_on(self):
        callback = lambda *a, **k: None
        self.agent.subscribe("Test.Interface", callback)
        sig, func = self.agent.sigs[-1]
        self.assertEqual(func, callback)
        self.assertEqual(sig.interface, ["Test", "Interface"])

    def test_wait(self):
        with Agent(self.bus) as agent:
            agent.publish("Test.Wait", "payload")
            payload, labels = self.agent.wait("Test.Wait", 1)
        self.assertEqual(payload, "payload")
