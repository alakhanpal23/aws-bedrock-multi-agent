import json, time

def handler(event,_):
    feeds = event.get("inputs",{}).get("feeds",[])
    # TODO: call real APIs; return normalized records
    return {"task_id": event.get("id","t2"), "records":[{"source":"hn","title":"Example","timestamp":int(time.time())}]}