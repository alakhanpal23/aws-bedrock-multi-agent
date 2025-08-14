import json, os, boto3

bedrock = boto3.client("bedrock-runtime", region_name=os.getenv("REGION"))

def call_llm(system, context_obj, user_msg, model_id=None, max_tokens=1000):
    model_id = model_id or os.getenv("REASONING_MODEL_ID")
    body = {
      "anthropic_version": "bedrock-2023-05-31",
      "max_tokens": max_tokens,
      "messages": [
        {"role":"system","content":system},
        {"role":"user","content":json.dumps({"context":context_obj,"message":user_msg})}
      ]
    }
    resp = bedrock.invoke_model(modelId=model_id, body=json.dumps(body))
    payload = json.loads(resp["body"].read())
    return payload["content"][0]["text"]