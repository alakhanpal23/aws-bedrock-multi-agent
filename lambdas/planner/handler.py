import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from common.bedrock_client import call_llm

SYSTEM = "You are a planning agent. Return STRICT JSON with a 'tasks' array."

def handler(event, _):
    goal = event.get("goal","Summarize today's AWS pricing changes.")
    plan = {
      "tasks":[
        {"id":"t1","type":"knowledge","inputs":{"query": goal},"deps":[]},
        {"id":"t2","type":"data","inputs":{"feeds":["aws_pricing","hn_top"]},"deps":["t1"]},
        {"id":"t3","type":"action","inputs":{"action":"recommend","constraints":{"budget":"low"}},"deps":["t1","t2"]}
      ]
    }
    return {"plan": plan}