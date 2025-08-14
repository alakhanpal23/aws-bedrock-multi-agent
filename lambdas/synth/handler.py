import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from common.bedrock_client import call_llm

def handler(event,_):
    tool_outputs = { "fanout": event.get("FanOutResults","(example)") }
    md = call_llm("Synthesize and cite.", tool_outputs, "create a short answer", max_tokens=400)
    return {"answer_md": md, "citations": []}