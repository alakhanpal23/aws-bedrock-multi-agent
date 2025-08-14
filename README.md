# AWS Bedrock Multi-Agent Orchestration Platform

## Quick Start

1. **Prerequisites**: Install AWS CLI v2, Python 3.11+, Docker, AWS SAM CLI
2. **Configure AWS**: `aws configure`
3. **Enable Bedrock models** in AWS Console:
   - `anthropic.claude-3-haiku-20240307-v1:0`
   - `amazon.titan-embed-text-v2:0`

## Deploy

```bash
cd infra
sam build
sam deploy --guided
```

## Initialize OpenSearch

```bash
OS="https://$(aws cloudformation describe-stacks --stack-name agent-platform --query "Stacks[0].Outputs[?OutputKey=='OpenSearchEndpoint'].OutputValue | [0]" --output text)"
curl -X PUT "$OS/documents_v1" -H 'Content-Type: application/json' --data-binary @opensearch-mappings.json
```

## Test

```bash
API=$(aws cloudformation describe-stacks --stack-name agent-platform --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue | [0]" --output text)
KEY=$(aws apigateway get-api-keys --include-values --query "items[?name=='agent-api-key'].value | [0]" --output text)

curl -X POST "$API/invoke" -H "x-api-key: $KEY" -H "Content-Type: application/json" \
  -d '{"goal":"Find current EC2 pricing tips for GPU batch compute and propose a weekly watch."}'
```