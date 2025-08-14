import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from common.retrieval import hybrid_search

def handler(event,_):
    q = event.get("inputs",{}).get("query","aws cloud cost")
    passages = hybrid_search(q, k=6)
    return {"task_id": event.get("id","t1"), "passages": passages, "citations":[{"title":p.get("title"),"url":p.get("url")} for p in passages]}