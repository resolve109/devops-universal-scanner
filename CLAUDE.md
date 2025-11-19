# CLAUDE.md - DevOps Universal Scanner v3.0

**AI Assistant Guide & Python 2025 Best Practices**

## Repository Overview

The DevOps Universal Scanner v3.0 is a **Pure Python 3.13** security scanning tool for Infrastructure as Code (IaC). It provides automated security analysis, FinOps intelligence, and CVE scanning using industry-standard tools with native intelligence layers.

### Key Characteristics (v3.0)
- **Language**: Pure Python 3.13 (NO bash scripts)
- **Architecture**: Multi-stage Docker build with Python 3.13 Alpine base
- **Distribution**: Docker Hub (`spd109/devops-uat`)
- **Purpose**: Multi-cloud IaC security + FinOps + AI/ML cost analysis + CVE scanning
- **Image Size**: ~600-700MB (30-40% smaller than v2.0)
- **Platform Support**: Multi-platform (linux/amd64, linux/arm64)

## Directory Structure (v3.0)

```
/
├── Dockerfile                      # Multi-stage optimized build
├── requirements.txt                # Python dependencies
├── README.md                       # User documentation
├── CLAUDE.md                       # This file (AI assistant guide)
├── ARCHITECTURE.md                 # Architecture documentation
├── CHANGELOG-v3.0.md               # Version 3.0 changelog
├── LICENSE                         # MIT License
├── .gitignore                      # Git ignore rules
│
└── devops_universal_scanner/       # Main Python package
    ├── __init__.py                 # Package initialization
    ├── __main__.py                 # CLI entry point (python -m devops_universal_scanner)
    ├── entrypoint.py               # Docker container entrypoint
    │
    ├── core/                       # Core scanning engine
    │   ├── __init__.py
    │   ├── scanner.py              # Main orchestrator (replaces ALL .sh scripts)
    │   ├── logger.py               # Dual logging (console + file)
    │   ├── tool_runner.py          # Base tool execution
    │   │
    │   ├── analyzers/              # Native intelligence analyzers
    │   │   ├── finops/             # FinOps cost analysis
    │   │   ├── aiml/               # AI/ML GPU optimization
    │   │   ├── security/           # Enhanced security checks
    │   │   └── reporting/          # Report generation
    │   │
    │   ├── cve/                    # CVE scanning
    │   │   ├── tool_cve_scanner.py
    │   │   ├── ami_cve_scanner.py
    │   │   └── image_cve_scanner.py
    │   │
    │   ├── pricing/                # Live pricing APIs
    │   │   ├── aws_pricing.py
    │   │   ├── azure_pricing.py
    │   │   └── gcp_pricing.py
    │   │
    │   ├── knowledge/              # Policy knowledge base
    │   │   ├── policy_loader.py
    │   │   └── custom_rules.py
    │   │
    │   ├── data/                   # Static data & cost estimates
    │   ├── helpers/                # Utility functions
    │   ├── rules/                  # Custom security rules
    │   ├── security/               # Security utilities
    │   ├── costs/                  # Cost calculation functions
    │   └── network/                # Network analysis
    │
    ├── docs/                       # Policy & tool documentation
    │   ├── 3.Custom Policies/
    │   ├── 4.Integrations/
    │   ├── 5.Policy Index/         # Checkov + all tool policies
    │   ├── 6.Contribution/
    │   ├── 7.Scan Examples/
    │   └── 8.Outputs/
    │
    └── test-files/                 # Vulnerable test templates
        ├── terraform/
        ├── cloudformation/
        ├── kubernetes/
        └── ...
```

---

## Python 2025 Best Practices

### Code Standards

#### 1. Type Hints (Required)
```python
from typing import Optional, List, Dict, Any
from pathlib import Path

def scan_terraform(target: Path, environment: str = "development") -> Dict[str, Any]:
    """
    Scan Terraform files for security issues

    Args:
        target: Path to Terraform file or directory
        environment: Environment type (development, staging, production)

    Returns:
        Dictionary containing scan results and statistics
    """
    results: Dict[str, Any] = {}
    return results
```

#### 2. Modern Path Handling
```python
from pathlib import Path

# ✅ GOOD - Use Path objects
config_file = Path("/app/config.yaml")
if config_file.exists():
    content = config_file.read_text(encoding="utf-8")

# ❌ BAD - Don't use os.path
import os
config_file = os.path.join("/app", "config.yaml")
```

#### 3. Dataclasses for Data Structures
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ScanResult:
    """Represents a security scan result"""
    severity: str
    message: str
    resource: str
    line_number: Optional[int] = None

    def is_critical(self) -> bool:
        return self.severity == "CRITICAL"
```

#### 4. Context Managers
```python
from pathlib import Path

# ✅ GOOD - Auto-cleanup with context manager
def write_report(file_path: Path, content: str) -> None:
    with file_path.open('w', encoding='utf-8') as f:
        f.write(content)

# ❌ BAD - Manual file handling
f = open(file_path, 'w')
f.write(content)
f.close()
```

#### 5. F-Strings for Formatting
```python
# ✅ GOOD - F-strings (Python 3.6+)
name = "terraform"
version = "1.5.0"
message = f"Scanning {name} version {version}"

# ❌ BAD - Old string formatting
message = "Scanning %s version %s" % (name, version)
message = "Scanning {} version {}".format(name, version)
```

#### 6. List/Dict Comprehensions
```python
# ✅ GOOD - Comprehensions
critical_issues = [issue for issue in issues if issue.severity == "CRITICAL"]
issue_counts = {severity: len([i for i in issues if i.severity == severity])
                for severity in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]}

# ❌ BAD - Loops for simple transformations
critical_issues = []
for issue in issues:
    if issue.severity == "CRITICAL":
        critical_issues.append(issue)
```

#### 7. Modern Error Handling
```python
from typing import Optional

# ✅ GOOD - Specific exceptions with context
def load_config(path: Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        logger.error(f"Config file not found: {path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {path}: {e}")
        return None

# ❌ BAD - Bare except
try:
    config = json.loads(path.read_text())
except:
    return None
```

#### 8. Enum for Constants
```python
from enum import Enum, auto

class Severity(Enum):
    """Security issue severity levels"""
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()

# Usage
if issue.severity == Severity.CRITICAL:
    alert_security_team()
```

#### 9. Async/Await for I/O Operations
```python
import asyncio
import aiohttp

async def fetch_pricing_data(url: str) -> dict:
    """Fetch pricing data asynchronously"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# Run multiple requests concurrently
async def get_all_pricing():
    aws_task = fetch_pricing_data(aws_url)
    azure_task = fetch_pricing_data(azure_url)
    gcp_task = fetch_pricing_data(gcp_url)

    results = await asyncio.gather(aws_task, azure_task, gcp_task)
    return results
```

#### 10. Structural Pattern Matching (Python 3.10+)
```python
def handle_scan_result(result: dict) -> str:
    match result:
        case {"severity": "CRITICAL", "auto_fix": True}:
            return apply_auto_fix(result)
        case {"severity": "CRITICAL"}:
            return alert_and_log(result)
        case {"severity": "HIGH" | "MEDIUM"}:
            return log_warning(result)
        case _:
            return log_info(result)
```

### Code Organization

#### Module Structure
```python
"""
Module docstring explaining purpose

Example:
    from devops_universal_scanner.core.scanner import Scanner

    scanner = Scanner("terraform", Path("./infra"))
    results = scanner.scan()
"""

# Standard library imports
import sys
from pathlib import Path
from typing import Optional, List

# Third-party imports
import boto3
import yaml

# Local imports
from devops_universal_scanner.core.logger import ScanLogger
from devops_universal_scanner.core.tool_runner import ToolRunner

# Module-level constants
DEFAULT_TIMEOUT = 300
MAX_RETRIES = 3

# Classes and functions
class Scanner:
    ...
```

#### Docstrings (Google Style)
```python
def analyze_costs(resources: List[dict], region: str = "us-east-1") -> Dict[str, float]:
    """
    Analyze infrastructure costs for given resources.

    Calculates monthly, weekly, daily, and hourly costs using live pricing
    APIs when available, falling back to static estimates.

    Args:
        resources: List of infrastructure resources to analyze
        region: AWS region for pricing data (default: us-east-1)

    Returns:
        Dictionary with cost breakdowns:
            - monthly_cost: Total monthly cost in USD
            - weekly_cost: Average weekly cost in USD
            - daily_cost: Average daily cost in USD
            - hourly_cost: Average hourly cost in USD

    Raises:
        ValueError: If resources list is empty
        PricingAPIError: If pricing API fails and no fallback available

    Example:
        >>> resources = [{"type": "aws_instance", "instance_type": "t3.large"}]
        >>> costs = analyze_costs(resources, region="us-west-2")
        >>> print(f"Monthly: ${costs['monthly_cost']:.2f}")
        Monthly: $60.74
    """
    if not resources:
        raise ValueError("Resources list cannot be empty")
    # Implementation...
```

### Performance Best Practices

#### 1. Use Generators for Large Datasets
```python
# ✅ GOOD - Generator for memory efficiency
def read_large_file(path: Path):
    with path.open('r') as f:
        for line in f:
            yield line.strip()

# ❌ BAD - Loading entire file into memory
def read_large_file(path: Path):
    with path.open('r') as f:
        return f.readlines()
```

#### 2. Cache Expensive Operations
```python
from functools import lru_cache
from typing import Optional

@lru_cache(maxsize=128)
def get_pricing_data(instance_type: str, region: str) -> Optional[float]:
    """Cache pricing lookups for 1 hour"""
    return fetch_from_api(instance_type, region)
```

#### 3. Use Sets for Membership Testing
```python
# ✅ GOOD - O(1) lookup
gpu_instances = {"p3.2xlarge", "p4d.24xlarge", "g5.xlarge"}
if instance_type in gpu_instances:
    analyze_gpu_costs()

# ❌ BAD - O(n) lookup
gpu_instances = ["p3.2xlarge", "p4d.24xlarge", "g5.xlarge"]
if instance_type in gpu_instances:
    analyze_gpu_costs()
```

### Security Best Practices

#### 1. Never Hardcode Credentials
```python
import os
from typing import Optional

# ✅ GOOD - Environment variables
def get_aws_credentials() -> tuple[Optional[str], Optional[str]]:
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    return access_key, secret_key

# ❌ BAD - Hardcoded
AWS_KEY = "AKIAIOSFODNN7EXAMPLE"  # NEVER DO THIS
```

#### 2. Validate Input
```python
from pathlib import Path

def scan_file(target: Path) -> dict:
    """Scan a file for security issues"""
    # Validate input exists
    if not target.exists():
        raise FileNotFoundError(f"Target not found: {target}")

    # Validate it's a file
    if not target.is_file():
        raise ValueError(f"Target must be a file: {target}")

    # Prevent directory traversal
    target = target.resolve()
    if not str(target).startswith("/work"):
        raise SecurityError("Access denied: outside work directory")

    # Proceed with scan
    return perform_scan(target)
```

#### 3. Sanitize Subprocess Commands
```python
import subprocess
import shlex

# ✅ GOOD - List arguments (no shell injection)
def run_tool(file_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["checkov", "-f", str(file_path)],
        capture_output=True,
        text=True,
        timeout=300
    )

# ❌ BAD - String command with shell=True
def run_tool(file_path: str):
    return subprocess.run(
        f"checkov -f {file_path}",  # VULNERABLE TO INJECTION!
        shell=True,
        capture_output=True
    )
```

### Testing Best Practices

#### 1. Write Testable Code
```python
# ✅ GOOD - Dependency injection
class Scanner:
    def __init__(self, tool_runner: ToolRunner, logger: ScanLogger):
        self.tool_runner = tool_runner
        self.logger = logger

    def scan(self, target: Path) -> dict:
        result = self.tool_runner.run_checkov(target)
        self.logger.message(f"Scanned {target}")
        return result

# Easy to test with mocks
def test_scanner():
    mock_runner = Mock(spec=ToolRunner)
    mock_logger = Mock(spec=ScanLogger)
    scanner = Scanner(mock_runner, mock_logger)
    # Test...
```

#### 2. Use Type Hints for Better Testing
```python
from typing import Protocol

class ToolRunnerProtocol(Protocol):
    """Interface for tool runners"""
    def run_checkov(self, target: Path) -> dict: ...
    def run_tflint(self, target: Path) -> dict: ...

# Any class implementing this protocol can be used
class Scanner:
    def __init__(self, tool_runner: ToolRunnerProtocol):
        self.tool_runner = tool_runner
```

---

## Code Review Checklist

When modifying code, ensure:

- [ ] **Type hints** on all function signatures
- [ ] **Docstrings** with Args, Returns, Raises sections
- [ ] **Path objects** instead of string paths
- [ ] **F-strings** for formatting
- [ ] **Context managers** for resource cleanup
- [ ] **Specific exceptions** (not bare except)
- [ ] **Input validation** for security
- [ ] **No hardcoded credentials**
- [ ] **Async/await** for I/O-bound operations
- [ ] **Generators** for large datasets
- [ ] **Caching** for expensive operations
- [ ] **List arguments** in subprocess calls (no shell=True)
- [ ] **Logging** at appropriate levels
- [ ] **Error messages** are helpful and actionable
- [ ] **No duplicate code** - DRY principle

---

## Common Patterns in This Codebase

### 1. Scanner Pattern
```python
class Scanner:
    """Main orchestrator for all scan types"""

    def __init__(self, scan_type: str, target: Path, environment: str = "development"):
        self.scan_type = scan_type
        self.target = target
        self.environment = environment
        self.logger = ScanLogger(self._get_log_file())
        self.tool_runner = ToolRunner(self.logger)

    def scan(self) -> int:
        """Run complete scan and return exit code"""
        self.logger.section(f"Starting {self.scan_type} scan")

        # Run base tools
        results = self._run_base_tools()

        # Run native intelligence
        insights = self._run_native_intelligence()

        # Generate summary
        self._generate_summary(results, insights)

        return self._calculate_exit_code(results)
```

### 2. Tool Runner Pattern
```python
@dataclass
class ToolResult:
    """Result from a tool execution"""
    tool_name: str
    exit_code: int
    stdout: str
    stderr: str
    duration: float

class ToolRunner:
    """Executes base security tools"""

    def run(self, tool_name: str, args: List[str]) -> ToolResult:
        start = time.time()
        result = subprocess.run(
            [tool_name] + args,
            capture_output=True,
            text=True,
            timeout=300
        )
        duration = time.time() - start

        return ToolResult(
            tool_name=tool_name,
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            duration=duration
        )
```

### 3. Knowledge Loader Pattern
```python
class PolicyKnowledgeLoader:
    """Loads policy documentation for offline use"""

    _instance: Optional['PolicyKnowledgeLoader'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.policies = self._load_policies()
            self.initialized = True

    def get_policy(self, policy_id: str) -> Optional[PolicyInfo]:
        return self.policies.get(policy_id)
```

---

## Extending the Scanner

### Adding a New Analyzer

1. Create module in appropriate subdirectory:
   ```
   devops_universal_scanner/core/analyzers/custom/my_analyzer.py
   ```

2. Follow the analyzer pattern:
   ```python
   from typing import Dict, List, Any
   from pathlib import Path

   class MyAnalyzer:
       """Custom analyzer for X"""

       def __init__(self):
           self.findings: List[Dict[str, Any]] = []

       def analyze(self, resources: List[dict]) -> Dict[str, Any]:
           """Analyze resources and return insights"""
           for resource in resources:
               if self._check_condition(resource):
                   self.findings.append({
                       "severity": "HIGH",
                       "message": "Found issue in resource",
                       "resource": resource['name']
                   })

           return {
               "findings": self.findings,
               "summary": self._generate_summary()
           }
   ```

3. Import in scanner.py and call in `_run_native_intelligence()`

### Adding a Custom Rule

1. Add to `core/knowledge/custom_rules.py`:
   ```python
   @dataclass
   class CustomRule:
       id: str
       name: str
       description: str
       severity: str
       resource_pattern: str  # Regex
       check_function: callable
       framework: str

   # Register in CustomRulesEngine
   engine.register_rule(CustomRule(
       id="CKV_CUSTOM_XXX_001",
       name="My custom rule",
       description="Checks for X",
       severity="MEDIUM",
       resource_pattern=r"aws_.*",
       check_function=my_check_function,
       framework="terraform"
   ))
   ```

---

## Debugging Tips

### 1. Enable Verbose Logging
```python
logger.setLevel(logging.DEBUG)
```

### 2. Test Individual Components
```python
# Test tool runner directly
from devops_universal_scanner.core.tool_runner import ToolRunner
from devops_universal_scanner.core.logger import ScanLogger

logger = ScanLogger()
runner = ToolRunner(logger)
result = runner.run_checkov(Path("./test.tf"))
print(result)
```

### 3. Use Python Debugger
```python
import pdb

def problematic_function():
    pdb.set_trace()  # Debugger stops here
    # Step through code
```

---

## Troubleshooting Common Issues

### Import Errors
```python
# ❌ ERROR: ModuleNotFoundError: No module named 'core'
from core.scanner import Scanner

# ✅ FIX: Use full package path
from devops_universal_scanner.core.scanner import Scanner
```

### Path Issues
```python
# ❌ ERROR: File not found (relative path issue)
config = Path("config.yaml")

# ✅ FIX: Use absolute or package-relative paths
config = Path(__file__).parent / "config.yaml"
```

### Docker Build Issues
```bash
# Ensure you're in the repository root
cd /home/user/devops-universal-scanner

# Build with proper context
docker build -t devops-scanner:v3 .

# Check PYTHONPATH in container
docker run --rm devops-scanner:v3 python3 -c "import sys; print(sys.path)"
```

---

## Version Control

### Commit Message Format
```
<type>: <short description>

<detailed description>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `test`: Adding tests
- `chore`: Maintenance

**Example**:
```
feat: Add GPU cost optimization analyzer

- Created GPUCostAnalyzer in core/analyzers/aiml/
- Detects P3, P4, G4, G5 instances
- Recommends spot instances for 70-90% savings
- Includes GPU-specific optimization strategies

Closes #123
```

---

**Version**: 3.0.0
**Python**: 3.13+
**Last Updated**: 2025-11-18
**Maintained By**: DevOps Security Team
