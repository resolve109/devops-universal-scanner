# AMI Alternative Suggestions - Implementation Checklist

**Feature**: Suggest working, latest AMI alternatives when CVEs are detected
**Status**: Planning → Implementation → Testing → Release
**Target Release**: v3.1.0

## Quick Start

This checklist provides a step-by-step guide to implementing the AMI alternative suggestions enhancement.

## Phase 1: Core Infrastructure ✅ (Completed)

- [x] Create `ami_alternative_finder.py` skeleton
- [x] Create `ami_alternatives.json` fallback database structure
- [x] Add `AMIAlternative` dataclass
- [x] Update `AMICVE` dataclass with alternatives field (commented out)
- [x] Add comprehensive implementation guide
- [x] Update CHANGELOG with planned enhancement

## Phase 2: Distribution Detection (2-3 hours)

### Task 2.1: Implement Distribution Pattern Matching
**File**: `ami_alternative_finder.py`
**Method**: `_detect_distribution()`

- [ ] Implement regex pattern matching for common distributions
- [ ] Test with sample AMI names:
  - Amazon Linux: `amzn2-ami-hvm-2.0.20250115-x86_64-gp2`
  - Amazon Linux 2023: `al2023-ami-2023.3.20250115.0-kernel-6.1-x86_64`
  - Ubuntu: `ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-20250115`
  - RHEL: `RHEL-9.3.0_HVM-20250115-x86_64-0-Hourly2-GP2`
  - Windows: `Windows_Server-2022-English-Full-Base-2025.01.15`
- [ ] Add fallback for unknown distributions
- [ ] Unit test coverage >90%

**Test Command**:
```python
python -m pytest devops_universal_scanner/core/cve/test_ami_alternative_finder.py::test_distribution_detection -v
```

### Task 2.2: Implement Fallback Database Loader
**File**: `ami_alternative_finder.py`
**Method**: `_load_fallback_database()`

- [ ] Load JSON from `core/data/ami_alternatives.json`
- [ ] Validate JSON structure
- [ ] Handle file not found gracefully
- [ ] Add error logging
- [ ] Cache loaded database in memory

**Test Command**:
```python
python -m pytest devops_universal_scanner/core/cve/test_ami_alternative_finder.py::test_fallback_database_loader -v
```

## Phase 3: AWS SSM Integration (3-4 hours)

### Task 3.1: Implement SSM Client Initialization
**File**: `ami_alternative_finder.py`
**Method**: `__init__()`

- [ ] Import boto3 with try/except for optional dependency
- [ ] Initialize SSM client with region
- [ ] Handle missing credentials gracefully
- [ ] Add logging for initialization status
- [ ] Set `use_aws_api = False` if initialization fails

**Test Command**:
```python
python -m pytest devops_universal_scanner/core/cve/test_ami_alternative_finder.py::test_ssm_initialization -v
```

### Task 3.2: Implement SSM Parameter Querying
**File**: `ami_alternative_finder.py`
**Method**: `_query_ssm_parameters()`

- [ ] Query SSM parameters for distribution/architecture
- [ ] Parse SSM response to extract AMI ID
- [ ] Handle SSM exceptions (NoSuchParameter, AccessDenied, etc.)
- [ ] Add response caching (1 hour TTL)
- [ ] Log API calls for debugging

**Example Code**:
```python
def _query_ssm_parameters(self, distribution: str, architecture: str) -> List[Dict]:
    if not self.ssm_client:
        return []

    param_path = self.SSM_PARAMETER_PATHS.get(distribution, {}).get(architecture)
    if not param_path:
        return []

    try:
        response = self.ssm_client.get_parameter(Name=param_path)
        ami_id = response['Parameter']['Value']
        return [{
            'ami_id': ami_id,
            'distribution': distribution,
            'architecture': architecture,
            'source': 'ssm',
            'last_updated': response['Parameter']['LastModifiedDate'].isoformat()
        }]
    except ClientError as e:
        self.logger.debug(f"SSM query failed: {e}")
        return []
```

**Test Command**:
```python
# With mocked boto3
python -m pytest devops_universal_scanner/core/cve/test_ami_alternative_finder.py::test_ssm_query_success -v
python -m pytest devops_universal_scanner/core/cve/test_ami_alternative_finder.py::test_ssm_query_failure -v
```

### Task 3.3: Implement Fallback Database Query
**File**: `ami_alternative_finder.py`
**Method**: `_query_fallback_db()`

- [ ] Query fallback database by distribution/architecture
- [ ] Extract AMI data for current region
- [ ] Return structured AMI info
- [ ] Handle missing data gracefully

**Test Command**:
```python
python -m pytest devops_universal_scanner/core/cve/test_ami_alternative_finder.py::test_fallback_query -v
```

## Phase 4: CVE Verification (2-3 hours)

### Task 4.1: Implement Basic CVE Verification
**File**: `ami_alternative_finder.py`
**Method**: `_verify_cve_free()`

- [ ] Check against known vulnerable AMI list
- [ ] Filter out AMIs with known CVEs
- [ ] Add verification status to results
- [ ] Log verification results

**Initial Implementation** (simple):
```python
def _verify_cve_free(self, alternatives: List[Dict]) -> List[Dict]:
    verified = []
    for alt in alternatives:
        # Check against known vulnerable AMIs
        if alt['ami_id'] not in self.KNOWN_VULNERABLE_AMIS:
            alt['verified_cve_free'] = True
            verified.append(alt)
        else:
            self.logger.debug(f"Filtered out vulnerable AMI: {alt['ami_id']}")
    return verified
```

**Test Command**:
```python
python -m pytest devops_universal_scanner/core/cve/test_ami_alternative_finder.py::test_cve_verification -v
```

### Task 4.2: (Optional) NVD API Integration
**File**: `ami_alternative_finder.py`
**Method**: `_verify_with_nvd()`

- [ ] Query NVD API for AMI-related CVEs
- [ ] Parse NVD response
- [ ] Cache results (24 hour TTL)
- [ ] Handle API rate limits
- [ ] Gracefully degrade if API unavailable

**Note**: This is optional for v3.1.0, can be added in v3.2.0

## Phase 5: Main Logic Implementation (2 hours)

### Task 5.1: Implement find_alternatives()
**File**: `ami_alternative_finder.py`
**Method**: `find_alternatives()`

- [ ] Call `_detect_distribution()`
- [ ] Try `_query_ssm_parameters()` if AWS API available
- [ ] Fall back to `_query_fallback_db()`
- [ ] Call `_verify_cve_free()`
- [ ] Convert to AMIAlternative objects
- [ ] Return top N suggestions
- [ ] Add comprehensive logging

**Example Implementation**:
```python
def find_alternatives(self, ami_id: str, ami_name: Optional[str] = None,
                     architecture: str = "x86_64", max_suggestions: int = 3) -> List[AMIAlternative]:
    alternatives = []

    # Detect distribution
    distribution = self._detect_distribution(ami_id, ami_name)
    if not distribution:
        self.logger.warning(f"Could not detect distribution for {ami_id}")
        # Return generic alternatives
        distribution = 'amazon_linux_2023'  # Default

    # Try AWS SSM first
    if self.use_aws_api and self.ssm_client:
        ssm_results = self._query_ssm_parameters(distribution, architecture)
        alternatives.extend(ssm_results)

    # Fall back to database
    if not alternatives:
        db_results = self._query_fallback_db(distribution, architecture)
        alternatives.extend(db_results)

    # Verify CVE-free
    alternatives = self._verify_cve_free(alternatives)

    # Convert to AMIAlternative objects
    ami_alternatives = []
    for alt in alternatives[:max_suggestions]:
        ami_alternatives.append(AMIAlternative(
            ami_id=alt['ami_id'],
            name=f"{alt['distribution']} {alt.get('version', 'latest')}",
            distribution=alt['distribution'],
            version=alt.get('version', 'latest'),
            region=self.region,
            architecture=architecture,
            last_updated=alt.get('last_updated'),
            verified_cve_free=alt.get('verified_cve_free', False)
        ))

    return ami_alternatives
```

**Test Command**:
```python
python -m pytest devops_universal_scanner/core/cve/test_ami_alternative_finder.py::test_find_alternatives -v
```

## Phase 6: Integration with AMICVEScanner (2 hours)

### Task 6.1: Update AMICVEScanner
**File**: `ami_cve_scanner.py`

- [ ] Import AMIAlternativeFinder
- [ ] Initialize finder in `__init__()`
- [ ] Uncomment `suggested_alternatives` field in AMICVE dataclass
- [ ] Call finder in `check_ami()` when CVEs detected
- [ ] Add alternatives to AMICVE object

**Example Code**:
```python
class AMICVEScanner:
    def __init__(self, region: str = "us-east-1", use_aws_api: bool = True):
        self.scan_results: List[AMICVE] = []
        self.alternative_finder = AMIAlternativeFinder(region=region, use_aws_api=use_aws_api)

    def check_ami(self, ami_id: str, ami_name: Optional[str] = None) -> AMICVE:
        # ... existing CVE checking logic ...

        result = AMICVE(
            ami_id=ami_id,
            ami_name=ami_name,
            has_cve=True,
            cve_ids=vuln_info["cves"],
            severity=vuln_info["severity"],
            recommendation=vuln_info["recommendation"]
        )

        # Find alternatives if CVEs detected
        if result.has_cve or result.is_outdated:
            alternatives = self.alternative_finder.find_alternatives(ami_id, ami_name)
            result.suggested_alternatives = alternatives

        return result
```

### Task 6.2: Update Report Generation
**File**: `ami_cve_scanner.py`
**Method**: `generate_report()`

- [ ] Uncomment alternative display logic
- [ ] Format alternatives nicely in report
- [ ] Add visual separators
- [ ] Test report formatting

**Test Command**:
```bash
python -m devops_universal_scanner cloudformation test-files/cloudformation/vulnerable-ami.yaml
```

## Phase 7: Testing (2-3 hours)

### Task 7.1: Unit Tests
**File**: `test_ami_alternative_finder.py` (new file)

- [ ] Test distribution detection (10+ cases)
- [ ] Test SSM querying (mocked boto3)
- [ ] Test fallback database loading
- [ ] Test fallback database querying
- [ ] Test CVE verification
- [ ] Test find_alternatives() workflow
- [ ] Test graceful degradation scenarios
- [ ] Test error handling

**Coverage Target**: >90%

**Run Tests**:
```bash
python -m pytest devops_universal_scanner/core/cve/test_ami_alternative_finder.py -v --cov
```

### Task 7.2: Integration Tests
**File**: `test_ami_cve_scanner_integration.py` (new file)

- [ ] Test full workflow with real templates
- [ ] Test with AWS API (if credentials available)
- [ ] Test offline mode (no AWS credentials)
- [ ] Test multi-region scenarios
- [ ] Test multiple architectures

**Run Tests**:
```bash
python -m pytest devops_universal_scanner/core/cve/test_ami_cve_scanner_integration.py -v
```

### Task 7.3: Manual Testing
**Test Files Needed**:
- CloudFormation with vulnerable AMI
- Terraform with vulnerable AMI
- Multi-region template
- ARM64 architecture AMI

**Manual Test Commands**:
```bash
# Test with CloudFormation
python -m devops_universal_scanner cloudformation test-files/cloudformation/vulnerable-ami.yaml

# Test with Terraform
python -m devops_universal_scanner terraform test-files/terraform/vulnerable-ami.tf

# Test with region override
python -m devops_universal_scanner cloudformation template.yaml --region us-west-2

# Test offline mode (no AWS credentials)
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY
python -m devops_universal_scanner cloudformation template.yaml
```

## Phase 8: Documentation (1 hour)

### Task 8.1: Update User Documentation
**Files to Update**:

- [ ] README.md - Add AMI alternatives feature
- [ ] ARCHITECTURE.md - Document new components
- [ ] docs/7.Scan Examples/ - Add example outputs
- [ ] CLAUDE.md - Update for AI assistants

### Task 8.2: Code Documentation
- [ ] Add comprehensive docstrings
- [ ] Add inline comments for complex logic
- [ ] Update type hints
- [ ] Add usage examples in docstrings

## Phase 9: Fallback Database Population (2 hours)

### Task 9.1: Query Latest AMI IDs
**Manual Process** (until automation is set up):

```bash
# Amazon Linux 2023
aws ssm get-parameter --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 --region us-east-1
aws ssm get-parameter --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64 --region us-east-1

# Ubuntu 24.04
aws ssm get-parameter --name /aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp2/ami-id --region us-east-1

# Ubuntu 22.04
aws ssm get-parameter --name /aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id --region us-east-1
```

- [ ] Query AMI IDs for us-east-1
- [ ] Query AMI IDs for us-west-2
- [ ] Query AMI IDs for eu-west-1
- [ ] Update ami_alternatives.json
- [ ] Verify all AMIs are accessible
- [ ] Add timestamps

### Task 9.2: Verify AMIs
- [ ] Launch test instances with each AMI
- [ ] Verify no known CVEs
- [ ] Verify AMIs are publicly accessible
- [ ] Document AMI sources

## Phase 10: Release Preparation (1 hour)

### Task 10.1: Pre-Release Checklist
- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] No TODOs in production code
- [ ] Code reviewed
- [ ] Fallback database populated

### Task 10.2: Docker Build & Test
```bash
# Build Docker image
docker build -t devops-scanner:v3.1.0 .

# Test in container
docker run --rm -v $(pwd)/test-files:/work devops-scanner:v3.1.0 cloudformation /work/cloudformation/vulnerable-ami.yaml

# Test with AWS credentials
docker run --rm -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -v $(pwd)/test-files:/work devops-scanner:v3.1.0 cloudformation /work/cloudformation/vulnerable-ami.yaml
```

- [ ] Docker build succeeds
- [ ] All tools available in container
- [ ] AMI alternatives working in container
- [ ] AWS SSM working with credentials
- [ ] Fallback working without credentials

### Task 10.3: Tag and Release
```bash
# Update version
git tag v3.1.0
git push origin v3.1.0

# Build and push Docker image
docker build -t spd109/devops-uat:v3.1.0 .
docker push spd109/devops-uat:v3.1.0
docker tag spd109/devops-uat:v3.1.0 spd109/devops-uat:latest
docker push spd109/devops-uat:latest
```

## Success Criteria

### Functional Requirements
- [x] Enhancement documented with comprehensive plan
- [ ] AMI alternatives suggested for vulnerable AMIs
- [ ] AWS SSM integration working
- [ ] Fallback database working
- [ ] CVE verification working
- [ ] Region-specific suggestions provided
- [ ] Multi-architecture support

### Quality Requirements
- [ ] Unit test coverage >90%
- [ ] Integration tests passing
- [ ] No regressions in existing functionality
- [ ] Documentation complete
- [ ] Code reviewed

### Performance Requirements
- [ ] SSM queries cached (no excessive API calls)
- [ ] Fallback database loaded once
- [ ] Suggestions returned in <1 second

## Estimated Timeline

| Phase | Estimated Hours | Status |
|-------|----------------|--------|
| Phase 1: Core Infrastructure | 2 hours | ✅ Complete |
| Phase 2: Distribution Detection | 2-3 hours | ⏳ Pending |
| Phase 3: AWS SSM Integration | 3-4 hours | ⏳ Pending |
| Phase 4: CVE Verification | 2-3 hours | ⏳ Pending |
| Phase 5: Main Logic | 2 hours | ⏳ Pending |
| Phase 6: Integration | 2 hours | ⏳ Pending |
| Phase 7: Testing | 2-3 hours | ⏳ Pending |
| Phase 8: Documentation | 1 hour | ⏳ Pending |
| Phase 9: Database Population | 2 hours | ⏳ Pending |
| Phase 10: Release | 1 hour | ⏳ Pending |
| **TOTAL** | **19-24 hours** | **5% Complete** |

## Next Steps

1. **Review this checklist** with the team
2. **Start with Phase 2** (Distribution Detection) - smallest, testable unit
3. **Set up test environment** with sample AMI IDs
4. **Create unit test file** with first test cases
5. **Implement incrementally** - one phase at a time
6. **Test continuously** - don't wait until the end

## Questions or Issues?

- Check `docs/ENHANCEMENT_AMI_ALTERNATIVES.md` for detailed design
- Review `ami_alternative_finder.py` for code structure
- Check `ami_cve_scanner.py` for integration points
- See CLAUDE.md for Python best practices

---

**Last Updated**: 2025-01-18
**Status**: Ready for Implementation
**Priority**: HIGH
