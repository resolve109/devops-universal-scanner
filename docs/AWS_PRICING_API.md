# AWS Pricing API Integration

## Overview

The DevOps Universal Scanner integrates with the AWS Pricing API to provide real-time cost estimates for AWS resources detected in your Infrastructure as Code templates.

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────┐
│  Scanner Initialization                             │
│  ├── Import aws_pricing.py                          │
│  ├── Create AWSPricingAPI() instance                │
│  └── _initialize_boto3()                            │
│      ├── Try: import boto3                          │
│      ├── Create pricing client                      │
│      ├── Test credentials with minimal API call     │
│      └── Set credentials_available = True/False     │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│  Cost Analysis (for each resource)                  │
│  └── get_ec2_pricing(instance_type, region)         │
│      ├── Check cache (1-hour TTL)                   │
│      ├── If credentials_available:                  │
│      │   └── Fetch from AWS Pricing API             │
│      └── Else: Use static fallback                  │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│  Result with Attribution                            │
│  ├── source: "aws_pricing_api" OR "static_fallback" │
│  ├── monthly_cost: $XX.XX                           │
│  ├── hourly_cost: $X.XXXX                           │
│  └── note: Explanation                              │
└─────────────────────────────────────────────────────┘
```

### Decision Flow

```
START
  │
  ├─→ boto3 installed?
  │   ├─→ NO  → Use static fallback (reason: "boto3 not installed")
  │   └─→ YES → Continue
  │
  ├─→ AWS credentials configured?
  │   ├─→ NO  → Use static fallback (reason: "No AWS credentials found")
  │   └─→ YES → Continue
  │
  ├─→ Test API call successful?
  │   ├─→ NO  → Use static fallback (reason: "AWS API test failed: [error]")
  │   └─→ YES → Continue
  │
  ├─→ Pricing data in cache?
  │   ├─→ YES → Return cached data (source: "aws_pricing_api")
  │   └─→ NO  → Continue
  │
  ├─→ Fetch from AWS Pricing API
  │   ├─→ SUCCESS → Cache and return (source: "aws_pricing_api")
  │   └─→ FAILURE → Use static fallback (reason: "API call failed")
  │
END
```

## Credential Configuration

### Method 1: Environment Variables (Recommended for Docker)

```bash
docker run -it --rm \
  -e AWS_ACCESS_KEY_ID='your-access-key' \
  -e AWS_SECRET_ACCESS_KEY='your-secret-key' \
  -v "$(pwd)":/work \
  spd109/devops-uat:latest \
  cloudformation /work/template.yaml
```

### Method 2: AWS CLI Configuration

```bash
# Configure credentials
aws configure
# AWS Access Key ID: your-access-key
# AWS Secret Access Key: your-secret-key
# Default region name: us-east-1
# Default output format: json

# Mount AWS credentials into container
docker run -it --rm \
  -v ~/.aws:/root/.aws:ro \
  -v "$(pwd)":/work \
  spd109/devops-uat:latest \
  cloudformation /work/template.yaml
```

### Method 3: IAM Role (EC2/ECS/Lambda)

If running in AWS compute environment with an IAM role attached:

```bash
# No credentials needed - boto3 uses instance metadata
docker run -it --rm \
  -v "$(pwd)":/work \
  spd109/devops-uat:latest \
  cloudformation /work/template.yaml
```

## Required IAM Permissions

Minimal IAM policy for pricing API access:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "pricing:GetProducts",
        "pricing:DescribeServices"
      ],
      "Resource": "*"
    }
  ]
}
```

**Note**: The AWS Pricing API is read-only and doesn't access your AWS account resources. It only retrieves public pricing information.

## Verifying Configuration

### Check Pricing API Status

The scanner outputs pricing API status in the summary:

```
PRICING DATA SOURCE:
   Provider: AWS
   Region: us-east-1
   API Status: Live API
   Live AWS Pricing API is active
```

or if using fallback:

```
PRICING DATA SOURCE:
   Provider: AWS
   Region: us-east-1
   API Status: Using Fallback
   AWS credentials not configured. No AWS credentials found
   How to configure: Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables, or configure with 'aws configure'
   Fallback data source: devops_universal_scanner/core/data/cost_estimates.py
```

### Run Test Script

```bash
# Inside container
python3 test_aws_pricing.py
```

Expected output with credentials:
```
AWS PRICING API INTEGRATION TEST
================================================================================

1. Initializing AWS Pricing API client...
   ✓ Client initialized

2. Checking API status...
   ✓ boto3 is installed
   ✓ AWS credentials are configured and valid

3. Testing EC2 instance pricing...
   ✓ t3.micro        :  $  7.59/mo  $0.0104/hr  (aws_pricing_api)
   ✓ t3.large        : $ 60.74/mo  $0.0832/hr  (aws_pricing_api)
   ✓ m5.xlarge       : $138.70/mo  $0.1900/hr  (aws_pricing_api)
   ✓ p3.2xlarge      : $2204.16/mo  $3.0192/hr  (aws_pricing_api)

✓ AWS Pricing API is ACTIVE - Live pricing data is being used
```

## Data Sources

### Live Pricing (Preferred)

When AWS credentials are available:

- **Source**: AWS Pricing API (`pricing.us-east-1.amazonaws.com`)
- **Services**: EC2, RDS
- **Update Frequency**: Real-time (cached for 1 hour)
- **Accuracy**: 100% accurate for current pricing
- **Region Support**: All AWS regions (via location mapping)
- **Attribution**: `source: "aws_pricing_api"`

### Static Fallback

When credentials are NOT available:

- **Source**: `devops_universal_scanner/core/data/cost_estimates.py`
- **Services**: EC2, RDS, EBS, S3, ALB/NLB, NAT Gateway, etc.
- **Update Frequency**: Manually updated (last update: 2025-11-18)
- **Accuracy**: Approximate (us-east-1 pricing as of last update)
- **Attribution**: `source: "static_fallback"`
- **Fallback Reason**: Shown in output

### Static Pricing Data

Location: `/mnt/e/github/devops-uat/devops-universal-scanner/devops_universal_scanner/core/data/cost_estimates.py`

Example:
```python
AWS_COST_ESTIMATES = {
    "aws_instance": {
        "t3.micro": 7.59,    # $/month
        "t3.large": 60.74,
        "m5.xlarge": 138.70,
        # ... more instance types
    },
    "aws_s3_bucket": {
        "standard": 0.023,   # $/GB/month
        "glacier": 0.004,
    },
    # ... more resource types
}
```

## Caching Behavior

### Cache Strategy

- **TTL**: 1 hour (3600 seconds) by default
- **Key Format**: `{service}_{instance_type}_{region}`
- **Examples**:
  - `ec2_t3.micro_us-east-1`
  - `rds_db.m5.large_eu-west-1`

### Cache Benefits

1. **Reduced API Calls**: Minimize AWS API requests
2. **Faster Scans**: Instant retrieval for cached prices
3. **Cost Savings**: Fewer API calls = lower costs
4. **Reliability**: Works during API outages (uses cache)

### Cache Invalidation

- Automatic after 1 hour
- Can be cleared by restarting the scanner

## Supported Resources

### Currently Implemented

| Resource Type | Live API | Static Fallback | Notes |
|---------------|----------|-----------------|-------|
| EC2 Instances | ✅ | ✅ | All instance types |
| RDS Instances | ✅ | ✅ | All DB instance classes |
| EBS Volumes | ❌ | ✅ | Static pricing only |
| S3 Buckets | ❌ | ✅ | Static pricing only |
| Load Balancers | ❌ | ✅ | ALB/NLB/Classic |
| NAT Gateway | ❌ | ✅ | Static pricing |

### Planned Enhancements

- [ ] Live EBS pricing from AWS API
- [ ] Live S3 pricing from AWS API
- [ ] Spot instance pricing
- [ ] Reserved instance pricing
- [ ] Savings Plans recommendations

## Troubleshooting

### Issue: Always Using Fallback Data

**Symptom**: Output shows "Using Fallback" even with credentials configured

**Solutions**:

1. **Verify boto3 is installed**:
   ```bash
   docker exec -it <container> python3 -c "import boto3; print(boto3.__version__)"
   ```

2. **Check credentials are passed to container**:
   ```bash
   docker exec -it <container> env | grep AWS_
   ```

3. **Test credentials manually**:
   ```bash
   docker exec -it <container> aws pricing describe-services --region us-east-1
   ```

4. **Check Docker logs**:
   ```bash
   docker logs <container> 2>&1 | grep -i "aws\|pricing\|credential"
   ```

### Issue: API Call Failures

**Symptom**: "AWS API test failed: [error]"

**Common Causes**:

1. **Network connectivity**: Firewall blocking `pricing.us-east-1.amazonaws.com`
2. **Invalid credentials**: Check access key and secret key
3. **Insufficient permissions**: Add `pricing:GetProducts` permission
4. **Rate limiting**: AWS API throttling (rare)

**Solutions**:

1. **Test network access**:
   ```bash
   curl -I https://pricing.us-east-1.amazonaws.com
   ```

2. **Validate credentials**:
   ```bash
   aws sts get-caller-identity
   ```

3. **Check IAM permissions**:
   ```bash
   aws iam get-policy-version --policy-arn <policy-arn> --version-id v1
   ```

### Issue: Incorrect Pricing Data

**Symptom**: Prices don't match AWS pricing page

**Possible Causes**:

1. **Using static fallback**: Check if live API is enabled
2. **Regional differences**: Pricing varies by region
3. **Reserved/Spot pricing**: Only On-Demand pricing is shown
4. **Cached data**: Old prices cached (1-hour TTL)

**Solutions**:

1. **Enable live API**: Configure AWS credentials
2. **Check region**: Ensure correct region in scan
3. **Restart scanner**: Clear cache

## Performance Considerations

### API Response Times

- **First call**: 500-1000ms (API request)
- **Cached call**: <1ms (in-memory)
- **Static fallback**: <1ms (dictionary lookup)

### Scan Impact

- **Small templates** (<10 resources): Negligible
- **Medium templates** (10-50 resources): 5-10 seconds overhead
- **Large templates** (>50 resources): 20-30 seconds overhead

### Optimization Tips

1. **Use caching**: Default 1-hour TTL reduces repeat calls
2. **Batch scans**: Scan multiple templates in one session (shared cache)
3. **Regional focus**: Specify region to avoid unnecessary lookups

## Security Best Practices

### Credential Management

1. **Never hardcode credentials** in templates or scripts
2. **Use IAM roles** when running in AWS (EC2/ECS/Lambda)
3. **Rotate credentials** regularly (90 days recommended)
4. **Use least privilege**: Only grant `pricing:GetProducts`
5. **Enable MFA** on IAM users accessing pricing API

### Docker Security

1. **Mount credentials read-only**: `-v ~/.aws:/root/.aws:ro`
2. **Use environment variables**: Easier to manage in CI/CD
3. **Don't commit credentials**: Add `.aws/` to `.gitignore`
4. **Use AWS Secrets Manager**: For automated deployments

## FAQ

### Q: Is the AWS Pricing API free?

**A**: Yes, the AWS Pricing API is free to use. There are no charges for API calls.

### Q: Do I need an AWS account?

**A**: Yes, you need AWS credentials (Access Key + Secret Key) from an AWS account. However, the pricing API doesn't access your account resources - it only retrieves public pricing information.

### Q: Which regions are supported?

**A**: All AWS commercial regions. The Pricing API is only available in us-east-1, but provides pricing for all regions.

### Q: How often is pricing updated?

**A**: AWS pricing changes are reflected in the Pricing API immediately. The scanner caches prices for 1 hour to optimize performance.

### Q: Can I use SSO/temporary credentials?

**A**: Yes, boto3 supports AWS SSO and temporary credentials from STS. Configure using `aws sso login` or use temporary credentials from STS.

### Q: What about AWS China or GovCloud?

**A**: The Pricing API doesn't cover China or GovCloud regions. Static fallback pricing is used for these regions.

## Additional Resources

- [AWS Pricing API Documentation](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/price-changes.html)
- [boto3 Pricing Client](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/pricing.html)
- [AWS Pricing Calculator](https://calculator.aws/)
- [Scanner Documentation](../README.md)

---

**Last Updated**: 2025-11-18
**Version**: 3.0.0
