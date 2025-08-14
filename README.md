# AWS Bedrock Multi-Agent Orchestration Platform

A serverless multi-agent system built on AWS that orchestrates intelligent workflows using Amazon Bedrock's Claude 3 Haiku and Titan embeddings, with OpenSearch for knowledge retrieval.

## 🏗️ Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│ API Gateway │───▶│ Step Functions│───▶│ Lambda Agents   │
└─────────────┘    └──────────────┘    └─────────────────┘
                           │                      │
                           ▼                      ▼
                   ┌──────────────┐    ┌─────────────────┐
                   │   Guardrail  │    │   Planner       │
                   │   Agent      │    │   Agent         │
                   └──────────────┘    └─────────────────┘
                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │ Knowledge Agent │◀──┐
                                    │ Data Agent      │   │
                                    │ Action Agent    │   │
                                    └─────────────────┘   │
                                              │           │
                                              ▼           │
                                    ┌─────────────────┐   │
                                    │ Synthesis Agent │   │
                                    └─────────────────┘   │
                                                          │
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐   │
│ OpenSearch  │◀───│ Embeddings   │◀───│ Knowledge Base  │───┘
│ Vector DB   │    │ (Titan v2)   │    │ Documents       │
└─────────────┘    └──────────────┘    └─────────────────┘

┌─────────────┐    ┌──────────────┐
│ DynamoDB    │    │ S3 Buckets   │
│ Tables      │    │ Artifacts    │
└─────────────┘    └──────────────┘
```

## 🚀 Features

- **Multi-Agent Orchestration**: Coordinated workflow execution via AWS Step Functions
- **Intelligent Planning**: Claude 3 Haiku-powered task decomposition and planning
- **Knowledge Retrieval**: Hybrid search combining vector similarity and BM25
- **Real-time Data Processing**: Configurable data source integration
- **Action Execution**: Automated task execution with artifact generation
- **Content Synthesis**: AI-powered response generation with citations
- **Security Guardrails**: Input validation and safety checks
- **Serverless Architecture**: Auto-scaling, pay-per-use infrastructure

## 📋 Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI v2** installed and configured
3. **AWS SAM CLI** for infrastructure deployment
4. **Python 3.11+** for local development
5. **Docker** for Lambda packaging

### Install Dependencies (macOS)

```bash
# Install via Homebrew
brew install awscli aws-sam-cli

# Or download directly
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
```

## 🔧 Setup

### 1. Configure AWS Credentials

```bash
aws configure
# Enter your Access Key ID, Secret Access Key, and preferred region
```

### 2. Enable Bedrock Models

In AWS Console → Amazon Bedrock → Model access, enable:
- `anthropic.claude-3-haiku-20240307-v1:0`
- `amazon.titan-embed-text-v2:0`

### 3. Deploy Infrastructure

```bash
cd infra
sam build
sam deploy --guided
```

Follow the prompts:
- Stack name: `agent-platform`
- Accept all defaults
- Allow SAM to create IAM roles: `Y`

### 4. Initialize OpenSearch Index

```bash
# Get OpenSearch endpoint from CloudFormation outputs
OS="https://$(aws cloudformation describe-stacks --stack-name agent-platform \
  --query "Stacks[0].Outputs[?OutputKey=='OpenSearchEndpoint'].OutputValue | [0]" \
  --output text)"

# Create the documents index
curl -X PUT "$OS/documents_v1" \
  -H 'Content-Type: application/json' \
  -u admin:TempPassword123! \
  --data-binary @opensearch-mappings.json
```

### 5. Configure API Gateway Usage Plan

```bash
# Get API ID from CloudFormation
API_ID=$(aws cloudformation describe-stacks --stack-name agent-platform \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue | [0]" \
  --output text | cut -d'/' -f3 | cut -d'.' -f1)

# Create usage plan
USAGE_PLAN_ID=$(aws apigateway create-usage-plan \
  --name agent-usage-plan \
  --api-stages apiId=$API_ID,stage=prod \
  --query 'id' --output text)

# Associate API key with usage plan
aws apigateway create-usage-plan-key \
  --usage-plan-id $USAGE_PLAN_ID \
  --key-id $(aws apigateway get-api-keys \
    --query "items[?name=='agent-api-key'].id | [0]" --output text) \
  --key-type API_KEY
```

## 🧪 Testing

### Get API Credentials

```bash
# Get API URL and Key
API_URL=$(aws cloudformation describe-stacks --stack-name agent-platform \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue | [0]" --output text)

API_KEY=$(aws apigateway get-api-keys --include-values \
  --query "items[?name=='agent-api-key'].value | [0]" --output text)

echo "API URL: $API_URL"
echo "API Key: $API_KEY"
```

### Test the Multi-Agent System

```bash
# Invoke the orchestrator
curl -X POST "$API_URL/invoke" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Find current EC2 pricing tips for GPU batch compute and propose optimization strategies"
  }'

# Check status
curl -X GET "$API_URL/status/request-123" \
  -H "x-api-key: $API_KEY"
```

## 🏛️ Infrastructure Components

| Component | Purpose | Configuration |
|-----------|---------|---------------|
| **API Gateway** | REST API endpoints | `/invoke`, `/status/{id}` |
| **Step Functions** | Workflow orchestration | Express workflows |
| **Lambda Functions** | Agent execution | 8 specialized agents |
| **OpenSearch** | Vector + text search | Fine-grained access control |
| **DynamoDB** | State management | 4 tables (requests, tasks, runs, profiles) |
| **S3 Buckets** | Document & artifact storage | Encrypted, private |
| **IAM Roles** | Least-privilege access | Bedrock, DynamoDB, S3, OpenSearch |

## 🤖 Agent Architecture

### Core Agents

1. **Guardrail Agent** (`lambdas/guardrail/`)
   - Input validation and safety checks
   - Prevents malicious or unsafe requests

2. **Planner Agent** (`lambdas/planner/`)
   - Decomposes complex goals into executable tasks
   - Creates dependency graphs for parallel execution

3. **Knowledge Agent** (`lambdas/knowledge/`)
   - Hybrid search across document corpus
   - Combines vector similarity + BM25 ranking

4. **Data Agent** (`lambdas/data/`)
   - Fetches real-time data from external APIs
   - Normalizes and structures information

5. **Action Agent** (`lambdas/action/`)
   - Executes tasks and generates artifacts
   - Stores results in S3 for persistence

6. **Synthesis Agent** (`lambdas/synth/`)
   - Combines agent outputs into coherent responses
   - Generates citations and references

### Common Utilities (`lambdas/common/`)

- **bedrock_client.py**: Claude 3 Haiku integration
- **embeddings.py**: Titan v2 text embeddings
- **retrieval.py**: Hybrid search implementation

## 🔒 Security Features

- **API Key Authentication**: Secure API access
- **IAM Least Privilege**: Minimal required permissions
- **VPC-Ready**: OpenSearch can be moved to private subnets
- **Encryption**: At-rest and in-transit encryption
- **Input Validation**: Guardrail agent prevents abuse
- **Fine-Grained Access**: OpenSearch security controls

## 📊 Monitoring & Observability

- **CloudWatch Logs**: All Lambda function logs
- **X-Ray Tracing**: Distributed request tracing
- **Step Functions Console**: Visual workflow monitoring
- **API Gateway Metrics**: Request/response analytics

## 🛠️ Development

### Local Testing

```bash
# Test individual Lambda functions
sam local invoke PlannerFn -e events/test-event.json

# Start local API
sam local start-api
```

### Adding New Agents

1. Create new Lambda function in `lambdas/new-agent/`
2. Add to `infra/template.yaml`
3. Update Step Functions definition
4. Deploy with `sam build && sam deploy`

## 🚀 Production Considerations

### Security Hardening

```bash
# Move OpenSearch to VPC
# Replace public access policy with VPC endpoints
# Enable SigV4 signing for OpenSearch requests
# Use AWS Secrets Manager for credentials
```

### Performance Optimization

- **Lambda Provisioned Concurrency**: For consistent latency
- **OpenSearch Reserved Instances**: For predictable workloads
- **DynamoDB On-Demand**: Auto-scaling for variable traffic
- **CloudFront**: CDN for static assets

### Cost Optimization

- **Step Functions Express**: Lower cost for high-volume workflows
- **Lambda ARM64**: Better price-performance ratio
- **S3 Intelligent Tiering**: Automatic storage optimization
- **Bedrock On-Demand**: Pay-per-token pricing

## 🧹 Cleanup

```bash
# Delete the entire stack
aws cloudformation delete-stack --stack-name agent-platform

# Clean up S3 buckets (if needed)
aws s3 rm s3://your-docs-bucket --recursive
aws s3 rm s3://your-artifacts-bucket --recursive
```

## 📚 Additional Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [AWS SAM Developer Guide](https://docs.aws.amazon.com/serverless-application-model/)
- [OpenSearch Service Guide](https://docs.aws.amazon.com/opensearch-service/)
- [Step Functions Developer Guide](https://docs.aws.amazon.com/step-functions/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Built with ❤️ using AWS Serverless Technologies**