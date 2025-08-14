import json, uuid, os, boto3
s3 = boto3.client("s3")
sfn = boto3.client("stepfunctions")

def handler(event,_):
    plan = {"recommended":"use g5.xlarge spot for batch CV","rationale":"lowest $/GPU-hr today"}
    key = f"plans/{uuid.uuid4()}.json"
    s3.put_object(Bucket=os.getenv("ARTIFACTS_BUCKET"), Key=key, Body=json.dumps(plan).encode())
    return {"task_id": event.get("id","t3"), "artifact_key": key, "plan": plan}

def invoke_entrypoint(event,_):
    request_id = str(uuid.uuid4())
    input_obj = {"goal": json.loads(event["body"]).get("goal","")}
    arn = os.environ.get("STATE_MACHINE_ARN")
    sfn.start_sync_execution(stateMachineArn=arn, input=json.dumps(input_obj))
    return {"statusCode":200,"headers":{"Content-Type":"application/json"},"body": json.dumps({"request_id":request_id,"status":"started"})}

def status_entrypoint(event,_):
    rid = event["pathParameters"]["request_id"]
    return {"statusCode":200,"headers":{"Content-Type":"application/json"},"body": json.dumps({"request_id":rid,"status":"(demo) complete"})}