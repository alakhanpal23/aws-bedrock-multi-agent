# AWS User Setup Guide

## Create New AWS User (if you don't have one)

### 1. Create AWS Account
- Go to https://aws.amazon.com
- Click "Create an AWS Account"
- Follow signup process (requires credit card)

### 2. Create IAM User for CLI Access

**In AWS Console:**
1. Go to IAM → Users → Create user
2. User name: `bedrock-developer`
3. Check "Provide user access to the AWS Management Console" (optional)
4. Next → Attach policies directly
5. Add these policies:
   - `PowerUserAccess` (for demo - gives broad permissions except IAM)
   - OR for production, use these specific policies:
     - `AmazonBedrockFullAccess`
     - `AmazonS3FullAccess`
     - `AmazonDynamoDBFullAccess`
     - `AmazonOpenSearchServiceFullAccess`
     - `AWSLambda_FullAccess`
     - `AmazonAPIGatewayAdministrator`
     - `AWSStepFunctionsFullAccess`
     - `CloudFormationFullAccess`
     - `IAMFullAccess`

### 3. Create Access Keys
1. Go to IAM → Users → bedrock-developer → Security credentials
2. Create access key → Command Line Interface (CLI)
3. Copy Access Key ID and Secret Access Key (keep these secure!)

### 4. Configure AWS CLI
```bash
aws configure
```
Enter:
- AWS Access Key ID: [paste your access key]
- AWS Secret Access Key: [paste your secret key]
- Default region: [your preferred region, e.g., us-west-2]
- Default output format: json

## Install Dependencies

### macOS:
```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install AWS CLI v2
brew install awscli

# Install SAM CLI
brew install aws-sam-cli

# Install Docker
brew install --cask docker
```

### Alternative (direct download):
```bash
# AWS CLI v2
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# SAM CLI
curl -L "https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-macos-x86_64.pkg" -o "aws-sam-cli.pkg"
sudo installer -pkg aws-sam-cli.pkg -target /
```

## Verify Installation
```bash
aws --version
sam --version
docker --version
python3 --version
```