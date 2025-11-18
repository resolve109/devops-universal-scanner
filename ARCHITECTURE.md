# DevOps Universal Scanner v3.0 - Architecture

## Pure Python 3.13 Engine - Complete Redesign

This document describes the architecture of the DevOps Universal Scanner v3.0, a complete rewrite from bash scripts to pure Python 3.13.

## 🎯 Design Principles

1. **Pure Python** - All scanning logic in Python 3.13, no bash scripts
2. **Single Responsibility** - Each module has one clear purpose
3. **No Duplicates** - One source of truth for everything
4. **Modular Architecture** - Everything organized under `core/`
5. **Cloud Friendly** - Optimized Docker image (~600-700MB, down from 1.02GB)

## 📁 Project Structure

```
devops-universal-scanner/
├── core/                          # Core engine - contains EVERYTHING
│   ├── __init__.py               # Core package initialization
│   ├── scanner.py                # Main orchestrator (replaces all .sh scanners)
│   ├── logger.py                 # Dual logging (console + file)
│   ├── tool_runner.py            # Base tool execution (checkov, tflint, etc.)
│   │
│   ├── analyzers/                # All analysis engines
│   │   ├── __init__.py
│   │   ├── result_parser.py     # Parse tool outputs
│   │   ├── aggregator.py        # Aggregate findings
│   │   ├── finops/              # Financial operations analysis
│   │   │   ├── cost_analyzer.py # Cost estimation
│   │   │   ├── optimization.py  # FinOps recommendations
│   │   │   └── idle_detector.py # Idle resource detection
│   │   ├── aiml/                # AI/ML specific analysis
│   │   │   ├── gpu_cost_analyzer.py
│   │   │   └── training_analyzer.py
│   │   ├── security/            # Enhanced security checks
│   │   │   └── enhanced_checks.py
│   │   └── reporting/           # Report generation
│   │       └── report_generator.py
│   │
│   ├── cve/                      # CVE scanning
│   │   ├── __init__.py
│   │   ├── tool_cve_scanner.py  # Scan installed tools
│   │   ├── ami_cve_scanner.py   # Scan AWS AMIs
│   │   └── image_cve_scanner.py # Scan container images
│   │
│   ├── pricing/                  # Live pricing APIs
│   │   ├── __init__.py
│   │   ├── aws_pricing.py       # AWS Pricing API
│   │   ├── azure_pricing.py     # Azure Pricing API
│   │   ├── gcp_pricing.py       # GCP Pricing API
│   │   └── pricing_cache.py     # Price caching layer
│   │
│   ├── data/                     # Static data & configurations
│   │   ├── __init__.py
│   │   └── cost_estimates.py    # Fallback cost estimates
│   │
│   ├── rules/                    # Custom security rules
│   │   └── __init__.py
│   │
│   ├── helpers/                  # Utility functions
│   │   ├── __init__.py
│   │   ├── docker_manager.py
│   │   ├── path_detector.py
│   │   └── result_processor.py
│   │
│   ├── security/                 # Security utilities
│   │   └── __init__.py
│   │
│   ├── network/                  # Network analysis
│   │   └── __init__.py
│   │
│   ├── costs/                    # Cost calculation functions
│   │   └── __init__.py
│   │
│   └── checkov_policies/         # Checkov policy index
│       └── __init__.py
│
├── cli.py                        # CLI entry point
├── entrypoint.py                 # Docker entrypoint (pure Python)
├── Dockerfile                    # Optimized multi-stage build
├── requirements.txt              # Python dependencies
├── setup.py                      # Package setup
├── README.md                     # User documentation
├── CLAUDE.md                     # AI assistant guide
├── ARCHITECTURE.md               # This file
└── test-files/                   # Test templates (intentionally vulnerable)
```

## 🏗️ Architecture Layers

### Layer 1: Entry Point
- **cli.py** - Command-line interface
- **entrypoint.py** - Docker container entrypoint

### Layer 2: Orchestration
- **core/scanner.py** - Main scanner orchestrator
  - Replaces ALL bash scanner scripts
  - Handles: terraform, cloudformation, docker, kubernetes, arm, bicep, gcp
  - Generates single log file per scan

### Layer 3: Tool Execution
- **core/tool_runner.py** - Runs base security tools
  - TFLint, TFSec, Checkov, CFN-Lint, etc.
  - Captures stdout, stderr, exit codes
  - Timestamps all outputs

### Layer 4: Native Intelligence
- **core/analyzers/** - Enhanced analysis beyond base tools
  - FinOps cost analysis
  - AI/ML GPU optimization
  - Security insights
  - Idle resource detection

### Layer 5: Supporting Services
- **core/cve/** - CVE scanning
- **core/pricing/** - Live pricing APIs
- **core/data/** - Static data and configs
- **core/helpers/** - Utility functions

## 🔄 Scan Flow

```
User Command
    ↓
cli.py / entrypoint.py
    ↓
core/scanner.py (orchestrator)
    ↓
    ├─→ core/tool_runner.py (base tools)
    │     ├─→ TFLint
    │     ├─→ TFSec
    │     ├─→ Checkov
    │     └─→ CFN-Lint
    ↓
    ├─→ core/analyzers/ (native intelligence)
    │     ├─→ Cost Analysis (live pricing)
    │     ├─→ FinOps Recommendations
    │     ├─→ GPU Cost Analysis
    │     └─→ Security Insights
    ↓
    ├─→ core/cve/ (CVE scanning)
    │     ├─→ Tool CVE Scanner
    │     ├─→ AMI CVE Scanner
    │     └─→ Image CVE Scanner
    ↓
core/logger.py (dual output)
    ├─→ Console (live feedback)
    └─→ Log File (complete record)
```

## 📊 Output Format

Each scan generates a single timestamped log file:
```
terraform-scan-report-20251118-143052.log
cloudformation-scan-report-20251118-143052.log
docker-scan-report-20251118-143052.log
```

Log structure:
1. **Header** - Scan metadata
2. **Base Tool Results** - TFLint, TFSec, Checkov, etc.
3. **Native Intelligence** - Cost analysis, optimizations, CVEs
4. **Summary** - Aggregated results and recommendations

## 🐳 Docker Image Optimization

### Size Reduction
- **Before**: 1.02GB
- **After**: ~600-700MB (30-40% reduction)

### Optimizations Applied
1. ✅ Removed Trivy (~150-200MB)
2. ✅ Removed Node.js + npm (~60MB)
3. ✅ Removed all bash scanner scripts (~2MB)
4. ✅ Multi-stage build (builder + runtime)
5. ✅ Python 3.13 Alpine base
6. ✅ Minimal runtime dependencies

### Build Stages
1. **Builder** - Compiles binaries, installs Python packages
2. **Runtime** - Minimal Alpine with only runtime dependencies

## 🛠️ Tools Included

### Security Scanners
- Checkov (multi-cloud)
- CFN-Lint (CloudFormation)
- TFLint (Terraform)
- TFSec (Terraform security)
- Bicep CLI (Azure)
- ARM-TTK (Azure)

### Cloud SDKs (for pricing APIs)
- boto3 (AWS)
- azure-mgmt-* (Azure)
- google-cloud-* (GCP)

## 🔐 Security Features

### CVE Scanning
- **Tool CVE Scanner** - Checks installed tools for vulnerabilities
- **AMI CVE Scanner** - Scans AWS AMI IDs for known CVEs
- **Image CVE Scanner** - Checks container image vulnerabilities

### Enhanced Checks
- Public exposure detection (0.0.0.0/0)
- Encryption verification
- Hardcoded credential detection
- Network security analysis

## 💰 FinOps Features

### Cost Analysis
- Live pricing from AWS/Azure/GCP APIs
- Fallback to static estimates
- Monthly/weekly/daily/hourly breakdowns

### Optimization Recommendations
- Business hours scheduling (73% savings)
- Reserved instances (40-60% savings)
- Spot instances (70-90% savings)
- Storage optimization (gp3 vs gp2)

### AI/ML Cost Analysis
- GPU instance detection (P3, P4, G4, G5)
- GPU-specific recommendations
- Training cost optimization

## 🚀 Usage

### Local Development
```bash
python3 cli.py terraform ./infrastructure
python3 cli.py cloudformation template.yaml
```

### Docker
```bash
# Build
docker build -t devops-scanner:v3 .

# Run
docker run --rm -v "$(pwd):/work" devops-scanner:v3 scan-terraform .
```

### Environment Options
```bash
--environment production  # For production-specific recommendations
--environment staging     # For staging environments
--environment development # Default
```

## 📦 Installation

### As Docker Image
```bash
docker pull spd109/devops-uat:latest
```

### As Python Package
```bash
pip install -e .
devops-scan terraform ./infra
```

## 🧪 Testing

Test files with intentional vulnerabilities are in `test-files/`:
```bash
docker run --rm -v "$(pwd):/work" devops-scanner:v3 scan-terraform test-files/terraform/
```

**⚠️ WARNING**: Never use test files in production!

## 🔧 Extensibility

### Adding a New Scanner Type
1. Add method to `core/scanner.py`: `_scan_<type>()`
2. Add command mapping in `cli.py` and `entrypoint.py`
3. Update help text

### Adding a New Analyzer
1. Create module in `core/analyzers/<category>/`
2. Import in `core/scanner.py`
3. Call in `_run_native_intelligence()`

### Adding Custom Rules
1. Add rules to `core/rules/`
2. Import in relevant analyzer
3. Update report generation

## 📝 Logging

### Dual Output System
- **Console**: Real-time feedback with emojis and colors
- **Log File**: Complete timestamped record

### Logger Methods
```python
logger.section()   # Section headers
logger.message()   # Info messages
logger.success()   # Success indicators
logger.warning()   # Warnings
logger.error()     # Errors
logger.tool_output()  # Raw tool output
```

## 🌟 Key Improvements Over v2.0

1. ✅ **Pure Python** - No bash scripts to maintain
2. ✅ **30-40% Smaller Image** - Removed unnecessary tools
3. ✅ **Live Pricing** - Real-time cost estimates
4. ✅ **CVE Scanning** - Comprehensive vulnerability checking
5. ✅ **Better Organization** - Everything in core/
6. ✅ **No Duplicates** - Single source of truth
7. ✅ **Claude Friendly** - Clean, well-documented code
8. ✅ **Faster Builds** - Optimized Docker layers
9. ✅ **Python 3.13** - Latest language features
10. ✅ **Type Hints** - Better IDE support

## 📚 Documentation

- **README.md** - User guide and quick start
- **CLAUDE.md** - AI assistant guide (updated for v3.0)
- **ARCHITECTURE.md** - This file (architecture overview)
- **SECURITY-UPDATE-SUMMARY.md** - Security changelog

## 🔄 Migration from v2.0

### Breaking Changes
- All bash scanner scripts removed
- New import paths: `core.*` instead of `analyzers.*`
- Different command structure (Python-based)

### Compatibility
- Same Docker volume mount: `-v "$(pwd):/work"`
- Same output format: timestamped `.log` files
- Same scan types: terraform, cloudformation, docker, etc.

---

**Version**: 3.0.0
**Python**: 3.13+
**Last Updated**: 2025-11-18
**Maintained By**: DevOps Security Team
