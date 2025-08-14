import re

def handler(event,_):
    goal = event.get("goal","")
    if re.search(r'(delete|drop|shutdown)\b', goal, re.I):
        raise Exception("Unsafe intent")
    return event