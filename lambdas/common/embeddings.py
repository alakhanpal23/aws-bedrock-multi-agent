import os, json, boto3
bedrock = boto3.client("bedrock-runtime", region_name=os.getenv("REGION"))

def embed(text: str):
    body = {"inputText": text}
    resp = bedrock.invoke_model(modelId=os.getenv("EMBEDDINGS_MODEL_ID"), body=json.dumps(body))
    return json.loads(resp["body"].read())["embedding"]