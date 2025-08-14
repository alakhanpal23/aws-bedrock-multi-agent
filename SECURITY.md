# Security Guidelines

## Sensitive Information

This repository contains example code and templates. Before deploying:

### 🔒 Required Configuration

1. **AWS Credentials**: Configure via `aws configure` or environment variables
2. **OpenSearch Credentials**: Set via environment variables:
   ```bash
   export OS_USERNAME=your-username
   export OS_PASSWORD=your-secure-password
   ```

### 🚫 Never Commit

- AWS Access Keys or Secret Keys
- API Keys or tokens
- OpenSearch passwords
- Specific resource ARNs or endpoints
- Account IDs or sensitive identifiers

### ✅ Safe Practices

- Use environment variables for sensitive data
- Use AWS IAM roles and policies
- Enable AWS CloudTrail for auditing
- Use AWS Secrets Manager for production secrets
- Rotate credentials regularly

### 🛡️ Production Security

- Deploy OpenSearch in VPC
- Use SigV4 signing for OpenSearch
- Enable encryption at rest and in transit
- Implement least-privilege IAM policies
- Monitor with CloudWatch and AWS Config

## Reporting Security Issues

Please report security vulnerabilities via GitHub Security Advisories.