# Enhancement: AMI Alternative Suggestions

**Status**: Planning / Not Yet Implemented
**Priority**: HIGH
**Estimated Effort**: 8-12 hours
**Risk Level**: Low (additive changes only)
**Business Value**: High (actionable security recommendations)

## Overview

When the AMI CVE scanner detects vulnerable or outdated AMIs, it currently provides generic recommendations like "Use latest Amazon Linux 2023 AMI". This enhancement will provide specific, verified AMI IDs that users can immediately use.

## Current Behavior

```
AMIs WITH KNOWN CVEs:
   [FAIL] ami-0abcdef1234567890
          CVEs: CVE-2024-12345
          Severity: HIGH
          Recommendation: Use latest Amazon Linux 2023 AMI
```

## Enhanced Behavior

```
AMIs WITH KNOWN CVEs:
   [FAIL] ami-0abcdef1234567890
          CVEs: CVE-2024-12345
          Severity: HIGH
          Recommendation: Use latest Amazon Linux 2023 AMI
          Suggested Alternatives:
            - ami-0abc123def456789a
              Amazon Linux 2023.3.20250115 (us-east-1)
              Last Updated: 2025-01-15
              Status: CVE-free (verified)
            - ami-0xyz987uvw654321b
              Ubuntu 24.04 LTS (us-east-1)
              Last Updated: 2025-01-14
              Status: CVE-free (verified)
            - ami-0def456ghi789012c
              Amazon Linux 2023.3.20250115 (us-west-2)
              Last Updated: 2025-01-15
              Status: CVE-free (verified)
```

## Architecture

### New Components

#### 1. AMIAlternativeFinder Class
**File**: `devops_universal_scanner/core/cve/ami_alternative_finder.py`

**Responsibilities**:
- Query AWS SSM Parameter Store for official AMI IDs
- Fall back to curated database when AWS API unavailable
- Detect AMI distribution from name/ID patterns
- Verify suggested AMIs are CVE-free
- Provide region-specific recommendations

**Key Methods**:
```python
class AMIAlternativeFinder:
    def find_alternatives(ami_id: str, ami_name: str, architecture: str) -> List[AMIAlternative]
    def _detect_distribution(ami_id: str, ami_name: str) -> str
    def _query_ssm_parameters(distribution: str, architecture: str) -> List[Dict]
    def _query_fallback_db(distribution: str, architecture: str) -> List[Dict]
    def _verify_cve_free(alternatives: List[Dict]) -> List[Dict]
```

#### 2. Fallback Database
**File**: `devops_universal_scanner/core/data/ami_alternatives.json`

**Structure**:
```json
{
  "metadata": {
    "last_updated": "2025-01-15T00:00:00Z",
    "version": "1.0.0"
  },
  "distributions": {
    "amazon_linux_2023": {
      "regions": {
        "us-east-1": {
          "x86_64": {
            "ami_id": "ami-...",
            "version": "2023.3.20250115",
            "verified_cve_free": true
          }
        }
      }
    }
  }
}
```

#### 3. Enhanced Data Classes
**File**: `devops_universal_scanner/core/cve/ami_cve_scanner.py`

**New Dataclass**:
```python
@dataclass
class AMIAlternative:
    ami_id: str
    name: str
    distribution: str
    version: str
    region: str
    architecture: str = "x86_64"
    last_updated: Optional[str] = None
    verified_cve_free: bool = False
```

**Enhanced Dataclass**:
```python
@dataclass
class AMICVE:
    # ... existing fields ...
    suggested_alternatives: List[AMIAlternative] = field(default_factory=list)
```

## Implementation Plan

### Phase 1: Core Infrastructure (3-4 hours)
1. ✅ Create `ami_alternative_finder.py` skeleton
2. ✅ Create `ami_alternatives.json` structure
3. ✅ Add `AMIAlternative` dataclass
4. ✅ Update `AMICVE` dataclass with alternatives field
5. Implement distribution detection logic
6. Implement fallback database loader

### Phase 2: AWS Integration (2-3 hours)
1. Implement SSM Parameter Store querying
2. Add boto3 error handling and graceful degradation
3. Implement region detection from template context
4. Add caching for SSM responses (avoid rate limits)

### Phase 3: CVE Verification (2-3 hours)
1. Integrate with existing CVE checking logic
2. Add NVD API integration (optional)
3. Implement verification workflow
4. Add confidence scoring for suggestions

### Phase 4: Integration & Testing (2-3 hours)
1. Integrate `AMIAlternativeFinder` into `AMICVEScanner.check_ami()`
2. Update `generate_report()` to display alternatives
3. Add CLI flag `--suggest-alternatives` (default: enabled)
4. Write unit tests
5. Write integration tests
6. Update documentation

## Dependencies

### Required
- `boto3` (already in requirements.txt)

### Optional
- `requests-cache` - For caching NVD API responses
- AWS credentials - For SSM parameter access (gracefully degrades)

## AWS SSM Parameter Paths

### Amazon Linux
```
/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64
/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64
/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2
/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-arm64-gp2
```

### Ubuntu
```
/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp2/ami-id
/aws/service/canonical/ubuntu/server/24.04/stable/current/arm64/hvm/ebs-gp2/ami-id
/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id
/aws/service/canonical/ubuntu/server/20.04/stable/current/amd64/hvm/ebs-gp2/ami-id
```

## Distribution Detection Patterns

```python
DISTRIBUTION_PATTERNS = {
    r'al2023|amazon.*linux.*2023': 'amazon_linux_2023',
    r'amzn2|amazon.*linux.*2(?!023)': 'amazon_linux_2',
    r'ubuntu.*24\.04|noble': 'ubuntu_24_04',
    r'ubuntu.*22\.04|jammy': 'ubuntu_22_04',
    r'ubuntu.*20\.04|focal': 'ubuntu_20_04',
    r'rhel.*9|red.*hat.*9': 'rhel_9',
    r'rhel.*8|red.*hat.*8': 'rhel_8',
    r'windows.*server.*2022': 'windows_server_2022',
    r'windows.*server.*2019': 'windows_server_2019',
    r'debian.*12|bookworm': 'debian_12',
    r'debian.*11|bullseye': 'debian_11',
    r'suse.*15': 'sles_15',
}
```

## Region Detection

Extract region from:
1. CloudFormation `Mappings` section
2. Terraform `provider` configuration
3. AMI ID region hints (if available)
4. Default to `us-east-1` with warning

## CLI Usage

```bash
# Default behavior (suggestions enabled)
python -m devops_universal_scanner cloudformation template.yaml

# Explicitly enable (default)
python -m devops_universal_scanner cloudformation template.yaml --suggest-alternatives

# Disable suggestions
python -m devops_universal_scanner cloudformation template.yaml --no-suggest-alternatives

# Specify region for suggestions
python -m devops_universal_scanner cloudformation template.yaml --region us-west-2
```

## Error Handling

### Graceful Degradation
1. **AWS API unavailable**: Fall back to curated database
2. **No credentials**: Skip AWS API, use fallback only
3. **Rate limiting**: Use cached results, show warning
4. **Distribution unknown**: Suggest general alternatives (AL2023, Ubuntu 24.04)
5. **Region unsupported**: Suggest nearest region or multi-region AMIs

### Error Messages
- Clear indication when using fallback vs. live data
- Warning when suggestions might be outdated
- Recommendation to configure AWS credentials for live data

## Testing Strategy

### Unit Tests
```python
def test_distribution_detection():
    """Test AMI distribution detection from name patterns"""

def test_ssm_parameter_query():
    """Test SSM parameter querying with mocked boto3"""

def test_fallback_database():
    """Test fallback database loading and querying"""

def test_cve_verification():
    """Test CVE verification logic"""

def test_region_detection():
    """Test region detection from templates"""
```

### Integration Tests
```python
def test_full_workflow():
    """Test complete AMI alternative suggestion workflow"""

def test_graceful_degradation():
    """Test fallback when AWS API unavailable"""

def test_multi_architecture():
    """Test x86_64 and arm64 suggestions"""
```

### Test Data
- Sample vulnerable AMIs
- Sample CloudFormation/Terraform templates
- Mocked SSM responses
- Mocked NVD API responses

## Maintenance

### Monthly Updates
Create GitHub Actions workflow to:
1. Query AWS SSM for latest AMI IDs
2. Verify each AMI is CVE-free
3. Update `ami_alternatives.json`
4. Create PR with changes
5. Run tests to validate

**File**: `.github/workflows/update-ami-database.yml` (to be created)

### Manual Updates
Document process for adding new distributions or regions:
1. Add distribution pattern to detection logic
2. Add SSM parameter path (if available)
3. Add fallback database entries
4. Update tests
5. Update documentation

## Documentation Updates

### Files to Update
1. `README.md` - Add AMI alternative suggestions feature
2. `ARCHITECTURE.md` - Document new components
3. `CHANGELOG-v3.0.md` - Add enhancement entry
4. `docs/7.Scan Examples/` - Add example outputs

### User Guide Section
```markdown
## AMI Security Scanning with Alternatives

When vulnerable or outdated AMIs are detected, the scanner provides:
- Specific CVE IDs and severity levels
- Verified, secure AMI alternatives
- Region-specific AMI IDs ready to use
- Architecture-aware suggestions (x86_64, arm64)

### Example Output
[Include screenshot or formatted example]

### Using AWS API for Live Suggestions
Configure AWS credentials to get real-time AMI suggestions:
[Include credential setup instructions]

### Offline Mode
Without AWS credentials, the scanner uses a curated database:
[Explain fallback behavior]
```

## Rollout Plan

### Version 3.1.0 Release
1. Implement core functionality
2. Add comprehensive tests
3. Update documentation
4. Beta testing with sample templates
5. Release to Docker Hub

### Feature Flags
- `AMI_SUGGESTIONS_ENABLED` - Enable/disable feature (default: true)
- `AMI_SUGGESTIONS_USE_AWS_API` - Use AWS API vs. fallback only (default: true)
- `AMI_SUGGESTIONS_MAX_COUNT` - Maximum suggestions per AMI (default: 3)

## Success Metrics

### User Impact
- Reduced time from detection to remediation
- Fewer user questions about "which AMI to use"
- Increased confidence in security posture

### Technical Metrics
- % of AMI findings with actionable suggestions
- % of suggestions from live API vs. fallback
- Cache hit rate for SSM queries
- Average suggestion accuracy

## Future Enhancements

### Phase 2 Features
1. **Cost comparison**: Show cost difference between current and suggested AMIs
2. **Performance benchmarks**: Include performance metrics for suggested AMIs
3. **Compliance mapping**: Match AMIs to compliance requirements (PCI-DSS, HIPAA, etc.)
4. **Auto-fix capability**: Generate IaC patches to replace vulnerable AMIs
5. **Change impact analysis**: Estimate impact of AMI replacement
6. **Custom AMI support**: Allow users to add their own curated AMI list

### Integration Opportunities
- AWS Systems Manager Patch Manager
- AWS Inspector findings
- AWS Security Hub
- Third-party vulnerability databases

## Questions & Decisions

### Open Questions
1. Should we cache AMI metadata locally to reduce API calls?
   - **Decision**: Yes, use 1-hour cache TTL
2. Should we support custom/private AMIs?
   - **Decision**: Phase 2, focus on official AMIs first
3. How many alternatives to suggest by default?
   - **Decision**: 3 (configurable)
4. Should we show cross-architecture alternatives?
   - **Decision**: Yes, show both x86_64 and arm64 if available

### Design Decisions
1. **Graceful degradation**: Always prefer working offline over failing
2. **Security first**: Only suggest verified CVE-free AMIs
3. **Region awareness**: Provide region-specific AMI IDs when possible
4. **User control**: Allow users to disable/customize suggestions

## References

### AWS Documentation
- [AWS SSM Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)
- [AWS Public Parameters](https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-public-parameters.html)
- [AMI Naming Conventions](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/finding-an-ami.html)

### Security Resources
- [NVD API](https://nvd.nist.gov/developers/vulnerabilities)
- [AWS Security Best Practices](https://docs.aws.amazon.com/security/)
- [CIS AWS Foundations Benchmark](https://www.cisecurity.org/benchmark/amazon_web_services)

### Related Issues
- GitHub Issue #XXX: AMI CVE scanning enhancement
- User request: Actionable AMI recommendations

---

**Last Updated**: 2025-01-18
**Author**: DevOps Universal Scanner Team
**Status**: Ready for Implementation
