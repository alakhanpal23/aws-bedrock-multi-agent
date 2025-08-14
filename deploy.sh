#!/bin/bash

# AWS Bedrock Multi-Agent Platform Deployment Script

set -e

echo "🚀 Starting AWS Bedrock Multi-Agent Platform Deployment"

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install AWS CLI v2"
    exit 1
fi

if ! command -v sam &> /dev/null; then
    echo "❌ SAM CLI not found. Please install AWS SAM CLI"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Run 'aws configure'"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Get deployment parameters
STACK_NAME=${1:-agent-platform}
REGION=${2:-$(aws configure get region)}

echo "📦 Deploying stack: $STACK_NAME in region: $REGION"

# Build the application
echo "🔨 Building SAM application..."
cd infra
sam build

# Deploy the application
echo "🚀 Deploying infrastructure..."
sam deploy \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --capabilities CAPABILITY_IAM \
    --no-confirm-changeset \
    --no-fail-on-empty-changeset

# Get outputs
echo "📊 Getting deployment outputs..."
API_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue | [0]" \
    --output text)

OS_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='OpenSearchEndpoint'].OutputValue | [0]" \
    --output text)

DOCS_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='DocsBucketName'].OutputValue | [0]" \
    --output text)

# Initialize OpenSearch
echo "🔍 Initializing OpenSearch index..."
curl -X PUT "https://$OS_ENDPOINT/documents_v1" \
    -H 'Content-Type: application/json' \
    -u admin:TempPassword123! \
    --data-binary @opensearch-mappings.json

# Create API Gateway usage plan
echo "🔑 Setting up API Gateway usage plan..."
API_ID=$(echo "$API_URL" | cut -d'/' -f3 | cut -d'.' -f1)

USAGE_PLAN_ID=$(aws apigateway create-usage-plan \
    --name "$STACK_NAME-usage-plan" \
    --api-stages apiId="$API_ID",stage=prod \
    --region "$REGION" \
    --query 'id' --output text 2>/dev/null || echo "exists")

if [ "$USAGE_PLAN_ID" != "exists" ]; then
    API_KEY_ID=$(aws apigateway get-api-keys \
        --region "$REGION" \
        --query "items[?name=='agent-api-key'].id | [0]" --output text)
    
    aws apigateway create-usage-plan-key \
        --usage-plan-id "$USAGE_PLAN_ID" \
        --key-id "$API_KEY_ID" \
        --key-type API_KEY \
        --region "$REGION" > /dev/null
fi

# Get API key
API_KEY=$(aws apigateway get-api-keys \
    --include-values \
    --region "$REGION" \
    --query "items[?name=='agent-api-key'].value | [0]" --output text)

# Upload sample document
echo "📄 Uploading sample document..."
echo "# AWS Cost Optimization Guide

This document contains best practices for optimizing AWS costs:

1. Use Reserved Instances for predictable workloads
2. Implement auto-scaling for variable workloads  
3. Use Spot Instances for fault-tolerant applications
4. Monitor and right-size your resources
5. Use S3 Intelligent Tiering for storage optimization

## EC2 Cost Tips
- Choose the right instance type for your workload
- Use placement groups for network-intensive applications
- Consider Graviton processors for better price-performance

## Storage Optimization
- Use S3 lifecycle policies
- Consider EBS gp3 volumes for better performance per dollar
- Use EFS Intelligent Tiering for file systems
" > sample-doc.txt

aws s3 cp sample-doc.txt "s3://$DOCS_BUCKET/guides/cost-optimization.txt"
rm sample-doc.txt

echo ""
echo "🎉 Deployment Complete!"
echo ""
echo "📋 Deployment Summary:"
echo "  Stack Name: $STACK_NAME"
echo "  Region: $REGION"
echo "  API URL: $API_URL"
echo "  OpenSearch: https://$OS_ENDPOINT"
echo "  Docs Bucket: $DOCS_BUCKET"
echo ""
echo "🔑 API Credentials:"
echo "  API Key: $API_KEY"
echo ""
echo "🧪 Test the API:"
echo "curl -X POST \"$API_URL/invoke\" \\"
echo "  -H \"x-api-key: $API_KEY\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"goal\":\"Find AWS cost optimization strategies for EC2 instances\"}'"
echo ""
echo "📚 Next Steps:"
echo "  1. Upload documents to s3://$DOCS_BUCKET/ for automatic indexing"
echo "  2. Test the multi-agent system with different goals"
echo "  3. Monitor CloudWatch logs for debugging"
echo "  4. Check Step Functions console for workflow visualization"
echo ""