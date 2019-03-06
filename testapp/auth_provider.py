import simplemb.rest
import uuid

agent = simplemb.rest.RestAgent("http://localhost:8000/", name="auth")

auth_table = {
    'bob': 'bob',
    'fred': 'fred'
}

tokens = []

def new_token():
    token = str(uuid.uuid4())
    tokens.append(token)
    return token

class UserPass:
    def __init__(self, user, password):
        self.user = user
        self.password = password

    @classmethod
    def deserialize(cls, msg):
        if type(msg.payload) == str:
            split = msg.payload.split('/',1)
            if len(split) == 2:
                return cls(*split)
        raise Exception

@agent.reply("Auth.Login")
def auth(msg):
    up = None
    try:
        up = UserPass.deserialize(msg)
    except:
        print(f"malformed login request {msg}")
        return None

    if auth_table.get(up.user) == up.password:
        print(f"returning new token for user {up.user}")
        return new_token()
    else:
        print(f"auth failed for user {up.user}")
        return None

@agent.reply("Auth.Validate")
def validate(msg):
    if msg.payload in tokens:
        print("token valid")
        return True
    else:
        print("token invalid")
        return False

agent.start()
print(f"Started uuid={agent.uuid}")
agent.join()