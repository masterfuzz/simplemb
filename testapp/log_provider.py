from simplemb.rest.restagent import RestAgent

logger = RestAgent("http://localhost:8000/", name="logger")

@logger.sub("**", consume=False)
def log(msg):
    print(f"{msg}")

logger.run()
# logger.join()
