"Agent" oriented

* An agent should be a single or small number of "areas of concern"
* The agent's tasks should be "atomic" in as much as a similar agent does not depend its state
* Should have a single or small number of "consumer" interfaces
* Should have a single "producer" interface

4 "directions" of input/output:

Produce:
* Publish: place a message on a named queue
* Reply: place a message on a temporary queue received from a previous request
Consume:
* Subscribe: listen and consume messages from a named queue
* Request: post a "request" message onto a temporary queue

Publish vs Request:
Publish posts messages to a queue which is expected to be persistent and consumed by any subscriber.
Request posts messages to ephemeral queues and expect a direct response

Reply vs Subscribe:

---

```
def do_things():
    # queue previously initialized with the interface
    publish(queue, things)

@reply(interface_name)
def respond_to_thing(thing):
    return response

@subscribe(queue_or_interface)
def compute(thing):
    pass

def do_other_things():
    response = request(interface, payload)
```

---

Interfaces:
a set of properties an object is expected to have.
A queue may say it contains objects that satisfy a particular interface.

an interface specification can be a particular property. So for example a queue could have LoggedInUser, and
a subscriber could subscribe to LoggedInUser.UUID and receive these objects.
A requester could post User.Authenticate and a replier on the interface User should be able to respond.


----

request -> special publish
-> reply (special subscribe) -> special publish
-> accept (special subscribe)

---

match queue:

Each subscription is a Path + Labels
Match = PathMatch and LabelMatch
PathMatch:
    A.B match A.B
    A.* match A.[anything]
    A.** match A.[any list]
LabelMatch:
    all labels exist and are the same. additional labels may exist in the message

One queue per "different" subscription.
    a subscription is different if the Path and the Labels are different
    

# Some DSL ideas...

* I want to "ask" remote services "questions"
* I want to "tell" remote services facts and "respond" to their questions
* i want to inform a group of interested services of events
..


# Event model


