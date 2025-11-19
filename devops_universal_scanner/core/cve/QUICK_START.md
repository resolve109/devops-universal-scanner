# AMI Alternative Suggestions - Quick Start Guide

**For developers implementing this enhancement**

## TL;DR

Add actionable AMI alternatives when CVEs are detected. Instead of "Use latest Amazon Linux 2023", show specific AMI IDs users can copy/paste.

## Files to Work With

### Core Implementation
```
devops_universal_scanner/core/cve/
├── ami_alternative_finder.py    ← Implement this (main work)
├── ami_cve_scanner.py           ← Integrate with this
└── IMPLEMENTATION_CHECKLIST.md  ← Follow this step-by-step
```

### Supporting Files
```
devops_universal_scanner/core/data/
└── ami_alternatives.json        ← Populate with real AMI IDs

devops_universal_scanner/docs/
├── ENHANCEMENT_AMI_ALTERNATIVES.md  ← Read this first
└── ami_enhancement_workflow.txt     ← Visual diagrams
```

## 5-Minute Overview

### What to Implement

1. **Distribution Detection** (easiest first)
   - Pattern match AMI names to distributions
   - Example: "amzn2-ami-hvm" → "amazon_linux_2"

2. **Fallback Database** (no AWS needed)
   - Load JSON file with curated AMI IDs
   - Query by distribution/region/architecture

3. **AWS SSM Integration** (requires credentials)
   - Query official AMI IDs from AWS
   - Cache results (1 hour TTL)

4. **CVE Verification**
   - Don't suggest AMIs with known CVEs
   - Cross-check against vulnerability list

5. **Integration**
   - Call from `AMICVEScanner.check_ami()`
   - Display in `generate_report()`

## Quick Start Commands

### Run Tests (create these first)
```bash
# Create test file
touch devops_universal_scanner/core/cve/test_ami_alternative_finder.py

# Run tests
python -m pytest devops_universal_scanner/core/cve/test_ami_alternative_finder.py -v

# With coverage
python -m pytest devops_universal_scanner/core/cve/test_ami_alternative_finder.py -v --cov
```

### Test Manually
```bash
# Test with CloudFormation template
python -m devops_universal_scanner cloudformation test-files/cloudformation/vulnerable-ami.yaml

# Test with specific region
python -m devops_universal_scanner cloudformation template.yaml --region us-west-2

# Test offline (no AWS credentials)
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY
python -m devops_universal_scanner cloudformation template.yaml
```

### Query Real AMI IDs
```bash
# Amazon Linux 2023 (x86_64)
aws ssm get-parameter \
  --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
  --region us-east-1 \
  --query 'Parameter.Value' \
  --output text

# Ubuntu 24.04 LTS (x86_64)
aws ssm get-parameter \
  --name /aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp2/ami-id \
  --region us-east-1 \
  --query 'Parameter.Value' \
  --output text

# Ubuntu 22.04 LTS (x86_64)
aws ssm get-parameter \
  --name /aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id \
  --region us-east-1 \
  --query 'Parameter.Value' \
  --output text
```

## Implementation Phases (Start Here)

### Phase 1: Distribution Detection (2-3 hours)
**Start with this - no AWS needed, easy to test**

```python
# In ami_alternative_finder.py
def _detect_distribution(self, ami_id: str, ami_name: Optional[str] = None) -> Optional[str]:
    if not ami_name:
        return None

    patterns = {
        r'al2023|amazon.*linux.*2023': 'amazon_linux_2023',
        r'amzn2|amazon.*linux.*2(?!023)': 'amazon_linux_2',
        r'ubuntu.*24\.04|noble': 'ubuntu_24_04',
        r'ubuntu.*22\.04|jammy': 'ubuntu_22_04',
        # Add more patterns
    }

    for pattern, distribution in patterns.items():
        if re.search(pattern, ami_name, re.IGNORECASE):
            return distribution

    return None
```

**Test**:
```python
# test_ami_alternative_finder.py
def test_detect_amazon_linux_2023():
    finder = AMIAlternativeFinder()
    dist = finder._detect_distribution("ami-123", "al2023-ami-kernel-default")
    assert dist == "amazon_linux_2023"

def test_detect_ubuntu_2404():
    finder = AMIAlternativeFinder()
    dist = finder._detect_distribution("ami-456", "ubuntu/images/hvm-ssd/ubuntu-noble-24.04")
    assert dist == "ubuntu_24_04"
```

### Phase 2: Fallback Database (2 hours)
**Second priority - still no AWS needed**

```python
# In ami_alternative_finder.py
def _load_fallback_database(self) -> Optional[Dict]:
    db_path = Path(__file__).parent.parent / "data" / "ami_alternatives.json"
    try:
        with open(db_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Fallback database not found: {db_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in fallback database: {e}")
        return None

def _query_fallback_db(self, distribution: str, architecture: str) -> List[Dict]:
    if not self.fallback_db:
        return []

    dist_data = self.fallback_db.get('distributions', {}).get(distribution, {})
    region_data = dist_data.get('regions', {}).get(self.region, {})
    ami_data = region_data.get(architecture)

    if ami_data:
        return [{
            'ami_id': ami_data['ami_id'],
            'distribution': distribution,
            'version': ami_data.get('version', 'unknown'),
            'architecture': architecture,
            'source': 'fallback_db',
            'last_updated': ami_data.get('last_updated'),
            'verified_cve_free': ami_data.get('verified_cve_free', False)
        }]

    return []
```

### Phase 3: AWS SSM Integration (3-4 hours)
**Requires AWS credentials, implement after Phases 1-2**

```python
# In ami_alternative_finder.py
def __init__(self, region: str = "us-east-1", use_aws_api: bool = True):
    self.region = region
    self.use_aws_api = use_aws_api
    self.ssm_client = None
    self.fallback_db = self._load_fallback_database()

    if use_aws_api:
        try:
            import boto3
            self.ssm_client = boto3.client('ssm', region_name=region)
            logger.info("AWS SSM client initialized")
        except Exception as e:
            logger.warning(f"Could not initialize AWS SSM client: {e}")
            self.use_aws_api = False

def _query_ssm_parameters(self, distribution: str, architecture: str) -> List[Dict]:
    if not self.ssm_client:
        return []

    param_path = self.SSM_PARAMETER_PATHS.get(distribution, {}).get(architecture)
    if not param_path:
        logger.debug(f"No SSM parameter path for {distribution}/{architecture}")
        return []

    try:
        response = self.ssm_client.get_parameter(Name=param_path)
        ami_id = response['Parameter']['Value']
        last_modified = response['Parameter']['LastModifiedDate']

        logger.info(f"Got AMI from SSM: {ami_id}")

        return [{
            'ami_id': ami_id,
            'distribution': distribution,
            'architecture': architecture,
            'source': 'ssm',
            'last_updated': last_modified.isoformat()
        }]

    except self.ssm_client.exceptions.ParameterNotFound:
        logger.warning(f"SSM parameter not found: {param_path}")
        return []
    except Exception as e:
        logger.error(f"SSM query failed: {e}")
        return []
```

### Phase 4: Integration (2 hours)

```python
# In ami_cve_scanner.py
class AMICVEScanner:
    def __init__(self, region: str = "us-east-1", use_aws_api: bool = True):
        self.scan_results: List[AMICVE] = []
        self.alternative_finder = AMIAlternativeFinder(region=region, use_aws_api=use_aws_api)

    def check_ami(self, ami_id: str, ami_name: Optional[str] = None) -> AMICVE:
        # Existing CVE checking logic
        if ami_id in self.KNOWN_VULNERABLE_AMIS:
            vuln_info = self.KNOWN_VULNERABLE_AMIS[ami_id]
            result = AMICVE(
                ami_id=ami_id,
                ami_name=ami_name,
                has_cve=True,
                cve_ids=vuln_info["cves"],
                severity=vuln_info["severity"],
                recommendation=vuln_info["recommendation"]
            )

            # NEW: Find alternatives
            alternatives = self.alternative_finder.find_alternatives(ami_id, ami_name)
            result.suggested_alternatives = alternatives

            return result

        # Rest of existing logic...
```

## Testing Checklist

### Unit Tests (Must Have)
- [ ] Distribution detection (10+ patterns)
- [ ] Fallback database loading
- [ ] Fallback database querying
- [ ] SSM querying (mocked boto3)
- [ ] CVE verification
- [ ] find_alternatives() workflow
- [ ] Error handling

### Integration Tests (Must Have)
- [ ] Full scan with vulnerable AMI
- [ ] Offline mode (no AWS credentials)
- [ ] AWS SSM mode (with credentials)
- [ ] Multi-region support
- [ ] Multi-architecture support

### Manual Tests (Before Release)
- [ ] CloudFormation scan with vulnerable AMI
- [ ] Terraform scan with vulnerable AMI
- [ ] Docker container test
- [ ] Various regions
- [ ] Various architectures

## Common Patterns

### Mock boto3 SSM in Tests
```python
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError

def test_ssm_query_success():
    with patch('boto3.client') as mock_boto3:
        mock_ssm = Mock()
        mock_ssm.get_parameter.return_value = {
            'Parameter': {
                'Value': 'ami-0abc123',
                'LastModifiedDate': datetime(2025, 1, 15)
            }
        }
        mock_boto3.return_value = mock_ssm

        finder = AMIAlternativeFinder()
        results = finder._query_ssm_parameters('amazon_linux_2023', 'x86_64')

        assert len(results) == 1
        assert results[0]['ami_id'] == 'ami-0abc123'

def test_ssm_query_failure():
    with patch('boto3.client') as mock_boto3:
        mock_ssm = Mock()
        mock_ssm.get_parameter.side_effect = ClientError(
            {'Error': {'Code': 'ParameterNotFound'}},
            'GetParameter'
        )
        mock_boto3.return_value = mock_ssm

        finder = AMIAlternativeFinder()
        results = finder._query_ssm_parameters('unknown_distro', 'x86_64')

        assert len(results) == 0
```

### Test Fallback Database
```python
def test_fallback_database_query():
    finder = AMIAlternativeFinder(region='us-east-1', use_aws_api=False)
    results = finder._query_fallback_db('amazon_linux_2023', 'x86_64')

    assert len(results) > 0
    assert 'ami_id' in results[0]
    assert results[0]['source'] == 'fallback_db'
```

## Debugging Tips

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check SSM Parameters Manually
```bash
# List all Amazon Linux AMI parameters
aws ssm get-parameters-by-path \
  --path /aws/service/ami-amazon-linux-latest \
  --region us-east-1

# List all Ubuntu parameters
aws ssm get-parameters-by-path \
  --path /aws/service/canonical/ubuntu \
  --region us-east-1
```

### Validate Fallback Database
```python
import json
from pathlib import Path

db_path = Path(__file__).parent.parent / "data" / "ami_alternatives.json"
with open(db_path) as f:
    data = json.load(f)
    print(json.dumps(data, indent=2))
```

## Common Issues

### Issue: boto3 not found
**Solution**: Already in requirements.txt, make sure Docker build succeeded

### Issue: SSM parameter not found
**Solution**: Check parameter path matches AWS documentation, some distributions may not be available

### Issue: No alternatives returned
**Solution**: Check distribution detection, verify fallback database has data for the region

### Issue: Tests fail with boto3 import
**Solution**: Mock boto3 in tests, don't require it for unit tests

## Next Steps After Implementation

1. **Test thoroughly** - All test suites must pass
2. **Populate database** - Get real AMI IDs from AWS
3. **Update docs** - Add examples to README
4. **Docker build** - Ensure it builds and runs
5. **Release** - Tag v3.1.0, push to Docker Hub

## Resources

- Full specification: `docs/ENHANCEMENT_AMI_ALTERNATIVES.md`
- Implementation checklist: `core/cve/IMPLEMENTATION_CHECKLIST.md`
- Workflow diagrams: `docs/ami_enhancement_workflow.txt`
- Code skeleton: `core/cve/ami_alternative_finder.py`
- Integration point: `core/cve/ami_cve_scanner.py`

## Questions?

Check the comprehensive documentation in:
- `ENHANCEMENT_AMI_ALTERNATIVES.md` - Design & architecture
- `IMPLEMENTATION_CHECKLIST.md` - Step-by-step tasks
- `ami_enhancement_workflow.txt` - Visual workflows

---

**Remember**: Start with Phase 1 (Distribution Detection) - it's the easiest and most testable!

**Target**: v3.1.0 release
**Estimated Effort**: 19-24 hours total
**Status**: Ready to implement
