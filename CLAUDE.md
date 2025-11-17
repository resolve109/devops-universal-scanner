# CLAUDE.md - DevOps Universal Scanner

**AI Assistant Guide for the DevOps Universal Scanner Repository**

## Repository Overview

The DevOps Universal Scanner is a comprehensive Docker-based security scanning tool for Infrastructure as Code (IaC) and container images. It provides automated security analysis for multiple cloud providers and IaC formats using industry-standard security scanning tools.

### Key Characteristics
- **Language Mix**: Bash (scanner scripts), Python (helper modules), Docker (containerization)
- **Architecture**: Multi-stage Docker build with Alpine Linux base
- **Distribution**: Docker Hub (`spd109/devops-uat`)
- **Purpose**: Security scanning and vulnerability detection for DevOps/IaC workflows
- **Platform Support**: Multi-platform (linux/amd64, linux/arm64)

## Directory Structure

```
devops-universal-scanner/
├── scanners/                    # Scanner shell scripts for each IaC type
│   ├── scan-terraform.sh       # Terraform scanner (TFLint, TFSec, Checkov)
│   ├── scan-cloudformation.sh  # AWS CloudFormation scanner
│   ├── scan-docker.sh          # Container image scanner (Trivy)
│   ├── scan-arm.sh             # Azure ARM template scanner
│   ├── scan-bicep.sh           # Azure Bicep scanner
│   ├── scan-gcp.sh             # GCP Deployment Manager scanner
│   └── scan-kubernetes.sh      # Kubernetes manifest scanner
│
├── helpers/                     # Python helper modules
│   ├── scanner_orchestrator.py # Coordinates scanner execution
│   ├── docker_manager.py       # Docker command builder and executor
│   ├── path_detector.py        # Cross-platform path detection
│   ├── result_processor.py     # Scan result processing
│   ├── scan-formatter.py       # Output formatting
│   └── checkov-processor.sh    # Checkov-specific processing
│
├── test-files/                 # Vulnerable test templates (DO NOT USE IN PROD)
│   ├── terraform/              # Test Terraform configs with vulnerabilities
│   ├── cloudformation/         # Test CloudFormation templates
│   ├── azure-arm/              # Test Azure ARM templates
│   ├── azure-bicep/            # Test Bicep templates
│   ├── gcp-deployment-manager/ # Test GCP templates
│   ├── kubernetes/             # Test Kubernetes manifests
│   └── docker/                 # Test Dockerfiles with issues
│
├── Dockerfile                  # Multi-stage Alpine-based build
├── docker-entrypoint.sh        # Container entry point with auto-detection
├── daily-update-manager.sh     # Intelligent security update system
├── uat-setup.sh                # UAT setup script
├── docker-tools-help.sh        # Help documentation
├── README.md                   # User-facing documentation
├── SECURITY-UPDATE-SUMMARY.md  # Security update history
└── CLAUDE.md                   # This file
```

## Architecture Overview

### Multi-Stage Docker Build

The project uses a multi-stage Docker build to minimize image size:

1. **Builder Stage** (Alpine 3.21.3):
   - Compiles binaries and installs tools
   - Installs Python packages with build dependencies
   - Downloads scanner tools (Terraform, TFLint, TFSec, Trivy, etc.)
   - Size optimization through temporary build environment

2. **Runtime Stage** (Alpine 3.21.3):
   - Only runtime dependencies
   - Copies compiled binaries from builder
   - Python virtual environment for isolation
   - ~1.02GB final image (35% smaller than original)

### Scanner Tools Included

| Category | Tools | Version Management |
|----------|-------|-------------------|
| **Terraform** | Terraform CLI, TFLint, TFSec, Checkov | Latest from GitHub releases |
| **AWS** | CFN-Lint, Checkov | Latest from pip/GitHub |
| **Azure** | Bicep CLI, ARM-TTK, Checkov | Latest from GitHub/git |
| **GCP** | Google Cloud Libraries, Checkov | Latest from pip |
| **Container** | Trivy | Latest from GitHub releases |
| **Kubernetes** | kube-score, Kubescape | Currently disabled (see Dockerfile) |

### Key Components

#### 1. Scanner Scripts (`scanners/*.sh`)

**Pattern**: All scanner scripts follow a consistent structure:

```bash
#!/bin/bash
set +e  # Don't exit on errors - handle gracefully

# Working directory setup
cd /work
TARGET="$1"
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
OUTPUT_PATH="/work/<type>-scan-report-${TIMESTAMP}.log"

# Logging functions
log_message() { ... }
log_success() { ... }
log_warning() { ... }
log_error() { ... }
log_section() { ... }

# Input validation
# Path normalization
# Tool execution with logging
# Summary generation
```

**Key Conventions**:
- All scripts accept a target (file/directory) as first argument
- Generate timestamped `.log` files with full output
- Use emoji indicators (✅ ⚠️ ❌) for visual feedback
- Exit codes are captured but don't halt execution
- All output is both displayed and logged to file

#### 2. Docker Entrypoint (`docker-entrypoint.sh`)

**Responsibilities**:
- Command routing to appropriate scanner
- Volume mount validation and helpful error messages
- Background security update management
- Cross-platform command examples in error messages
- Tool wrapper execution

**Command Flow**:
```
User command → Entrypoint → Volume check → Scanner script → Tool execution → Log file
```

#### 3. Helper Modules (`helpers/*.py`)

**scanner_orchestrator.py**:
- Coordinates scanner execution
- Maps commands to scanner scripts
- Validates scanner availability
- Provides scanner metadata

**path_detector.py**:
- Cross-platform path detection (Windows/Linux/macOS)
- Docker volume mount formatting
- Path validation and resolution
- Container path translation

**docker_manager.py**:
- Docker availability checking
- Command building for Docker execution
- Container image management
- Docker command execution

**result_processor.py**:
- Scan result parsing
- Finding aggregation
- Report generation

#### 4. Update Management (`daily-update-manager.sh`)

**Intelligent Caching System**:
- Updates security packages once per day (not every run)
- Timestamp-based caching in `/var/cache/devops-scanner/`
- Background updates don't block container usage
- Comprehensive logging to `/var/log/devops-scanner/updates.log`

**Commands**:
- `update-status` - Show current update status and tool versions
- `update-force` - Force immediate security updates
- `update-help` - Display update manager help

## Development Workflows

### Building the Docker Image

```bash
# Standard build
docker build -t spd109/devops-uat:latest .

# Multi-platform build (requires buildx)
docker buildx build --platform linux/amd64,linux/arm64 -t spd109/devops-uat:latest .

# Build with date tag
docker build -t spd109/devops-uat:$(date +%Y%m%d) .
```

**Build Time**: ~1.1 minutes (56% faster than original)
**Image Size**: ~1.02GB (35.4% smaller than original)

### Testing Scanners

```bash
# Test Terraform scanner
docker run --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform test-files/terraform/

# Test CloudFormation scanner
docker run --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-cloudformation test-files/cloudformation/ec2-instance.yaml

# Test Docker image scanner (no volume needed)
docker run --rm spd109/devops-uat:latest scan-docker nginx:latest

# Run all tests
for scanner in terraform cloudformation docker arm bicep gcp kubernetes; do
    echo "Testing $scanner..."
    # Run appropriate test
done
```

### Adding a New Scanner

1. **Create scanner script** in `scanners/scan-<name>.sh`:
   ```bash
   #!/bin/bash
   set +e
   cd /work
   TARGET="$1"
   TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
   OUTPUT_PATH="/work/<name>-scan-report-${TIMESTAMP}.log"

   # Add logging functions
   # Add validation
   # Add tool execution
   # Add summary
   ```

2. **Install tools** in `Dockerfile`:
   - Add to builder stage if compilation needed
   - Add to runtime stage for runtime-only tools
   - Create symbolic links in `/usr/local/bin/`

3. **Update entrypoint** in `docker-entrypoint.sh`:
   ```bash
   case "$COMMAND" in
       scan-<name>)
           exec /usr/local/bin/tools/scan-<name>.sh "$@"
           ;;
   esac
   ```

4. **Add to orchestrator** in `helpers/scanner_orchestrator.py`:
   ```python
   self.scanner_commands = {
       '<name>': 'scan-<name>',
       # ...
   }
   ```

5. **Create test files** in `test-files/<name>/`

6. **Update documentation** in `README.md`

## Code Conventions

### Bash Scripts

1. **Error Handling**:
   ```bash
   set +e  # Don't exit on errors - handle gracefully
   # Capture exit codes
   TOOL_EXIT=$?
   # Log based on exit code
   ```

2. **Logging**:
   - Always use logging functions (`log_message`, `log_success`, etc.)
   - Include timestamps in all log entries
   - Use emoji indicators for quick visual feedback
   - Both display and append to log file

3. **Path Handling**:
   ```bash
   # Remove /work/ prefix if provided
   TARGET=$(echo "$TARGET" | sed 's|^/work/||')

   # Check existence before use
   if [ ! -e "$TARGET" ]; then
       log_error "Target '$TARGET' not found!"
       exit 1
   fi
   ```

4. **Variable Naming**:
   - ALL_CAPS for constants and environment variables
   - lowercase_with_underscores for local variables
   - Descriptive names (not single letters)

### Python Modules

1. **Class Design**:
   - Single responsibility principle
   - Type hints for function parameters and returns
   - Docstrings for all public methods

2. **Error Handling**:
   ```python
   try:
       # Operation
   except Exception as e:
       print(f"❌ Error: {e}")
       return False
   ```

3. **Cross-Platform Support**:
   ```python
   import platform
   self.platform = platform.system().lower()
   self.is_windows = self.platform == 'windows'
   ```

### Dockerfile

1. **Multi-Stage Pattern**:
   ```dockerfile
   FROM alpine:3.21.3 AS builder
   # Build dependencies

   FROM alpine:3.21.3
   # Runtime only
   COPY --from=builder /compiled/binaries /destination/
   ```

2. **Layer Optimization**:
   - Combine related RUN commands with `&&`
   - Clean up in same layer as installation
   - Remove .git directories and docs

3. **Security**:
   - Use specific version tags (not `latest` for base images)
   - Run as non-root where possible (currently root for tool compatibility)
   - Regular security updates via update manager

## Testing Strategy

### Test Files

**CRITICAL**: All files in `test-files/` contain **intentional security vulnerabilities** for testing purposes.

**DO NOT**:
- Use test files in production
- Deploy test templates to cloud providers
- Copy test patterns to real infrastructure

**Purpose**:
- Validate scanner detection capabilities
- Test all security check categories
- Provide reproducible test cases

### Test Categories

Each test file category tests specific vulnerabilities:

1. **Authentication & Authorization**:
   - Hardcoded credentials
   - Weak passwords
   - Overly permissive IAM

2. **Network Security**:
   - 0.0.0.0/0 access rules
   - Public subnets
   - Missing VPC flow logs

3. **Data Protection**:
   - Unencrypted storage
   - Public read/write access
   - No backup encryption

4. **Monitoring & Logging**:
   - Disabled audit logging
   - No security monitoring

5. **Configuration Security**:
   - Debug modes enabled
   - Default configurations
   - Insecure protocols

## Security Considerations

### CVEs Addressed

The project actively addresses security vulnerabilities:

1. **CVE-2025-47273** (setuptools): Updated to >= 75.0.0
2. **CVE-2024-29415** (npm ip): Updated to latest
3. **CVE-2024-21538** (cross-spawn): Updated to latest
4. **CVE-2022-25883** (semver): Updated to latest
5. **CVE-2024-28863** (tar): Updated to latest
6. **CVE-2025-24359** (asteval): Updated to latest

See `SECURITY-UPDATE-SUMMARY.md` for complete details.

### Update Management

**Daily Update System**:
- Checks for updates once per day (timestamp-based)
- Background updates don't block container startup
- Logs all updates to `/var/log/devops-scanner/updates.log`
- Graceful fallback if updates fail

### Credential Handling

**Git Ignore Patterns**:
```gitignore
# Docker Hub credentials
dockerhub-credentials.txt
*.token

# Cloud credentials
aws-credentials.txt
.aws/

# Environment files
.env
*.env
```

**Never commit**:
- API keys or tokens
- Cloud provider credentials
- Docker Hub credentials
- Any `.env` files

## Common Tasks

### Running Scans Locally

```bash
# From repository root
docker build -t devops-uat-local .

# Test with local files
docker run --rm -v "$(pwd):/work" devops-uat-local scan-terraform test-files/terraform/

# Debug mode (interactive shell)
docker run -it --rm -v "$(pwd):/work" devops-uat-local /bin/bash
```

### Debugging Scanner Issues

1. **Check volume mount**:
   ```bash
   docker run --rm -v "$(pwd):/work" spd109/devops-uat:latest ls -la /work
   ```

2. **Run scanner with verbose output**:
   - Scanners already log all output to `.log` files
   - Check the generated log file for details

3. **Interactive debugging**:
   ```bash
   docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest /bin/bash
   cd /work
   /usr/local/bin/tools/scan-terraform.sh test-files/terraform/
   ```

4. **Check tool versions**:
   ```bash
   docker run --rm spd109/devops-uat:latest update-status
   ```

### Updating Documentation

1. **README.md**: User-facing documentation
   - Keep examples current
   - Update version numbers
   - Add new scanner commands

2. **CLAUDE.md**: This file (AI assistant guide)
   - Update when architecture changes
   - Add new patterns and conventions
   - Document new workflows

3. **SECURITY-UPDATE-SUMMARY.md**: Security changelog
   - Add CVE fixes
   - Document security improvements
   - Track version updates

## Git Workflow

### Branch Strategy

- **Main branch**: Stable releases
- **Development branches**: Feature development (often named with `claude/` prefix for AI sessions)
- **Pull requests**: Required for merging to main

### Commit Messages

Follow conventional commits:
```
feat: Add new GCP scanner support
fix: Resolve volume mount issue on Windows
docs: Update scanner command examples
security: Address CVE-2025-XXXXX in dependency
refactor: Optimize Docker layer caching
```

### Important Notes

1. **kube-score and Kubescape**: Currently disabled in Dockerfile (lines 65-73)
   - Created as stub scripts to prevent errors
   - Can be re-enabled when issues are resolved

2. **Scan Reports**: Generated `.log` files are intentionally NOT in `.gitignore`
   - Some example reports are committed for reference
   - Don't commit real security scan results from production

## Troubleshooting Guide

### "Docker not found" Error

**Cause**: Docker not in system PATH or not running

**Solution**:
1. Verify Docker is installed: `docker --version`
2. Check Docker is running: `docker info`
3. On Windows, add to PATH:
   - `C:\Program Files\Docker\Docker\resources\bin`
   - Restart terminal after PATH change

### "Volume mount failed" Error

**Cause**: Incorrect volume mount syntax or permissions

**Solution**:
- Windows PowerShell: `${PWD}:/work`
- Windows CMD: `%cd%:/work`
- Linux/macOS: `$(pwd):/work`
- Ensure you're in correct directory with your files

### "No files found" in Container

**Cause**: Volume mount not applied or wrong path

**Solution**:
1. Check current directory: `pwd` or `cd`
2. Verify files exist: `ls terraform/`
3. Use correct volume mount flag: `-v "$(pwd):/work"`

### Scanner Not Finding Issues

**Cause**: May be testing against clean code or tool version issue

**Solution**:
1. Test with provided vulnerable files: `test-files/`
2. Check tool versions: `update-status`
3. Force update tools: `update-force`
4. Verify scanner is appropriate for file type

## AI Assistant Guidelines

### When Making Changes

1. **Always read existing files first** before modifying
2. **Follow existing patterns** in similar files
3. **Test changes** with provided test files
4. **Update documentation** when adding features
5. **Check security implications** of any changes

### Code Modification Best Practices

1. **Scanner Scripts**:
   - Maintain logging consistency
   - Preserve error handling patterns
   - Keep exit code behavior
   - Update timestamp in outputs

2. **Dockerfile**:
   - Preserve multi-stage structure
   - Maintain layer optimization
   - Test build after changes
   - Check final image size

3. **Python Helpers**:
   - Add type hints
   - Include docstrings
   - Handle cross-platform differences
   - Add error handling

### Common Pitfalls to Avoid

1. **Don't break volume mounting** - This is critical functionality
2. **Don't remove error handling** - Scripts should fail gracefully
3. **Don't commit credentials** - Check `.gitignore` compliance
4. **Don't use test files as examples** - They contain vulnerabilities
5. **Don't skip documentation updates** - Keep README and CLAUDE.md in sync

### Useful File References

- **Scanner pattern**: `scanners/scan-terraform.sh` (most complete example)
- **Entrypoint logic**: `docker-entrypoint.sh` (command routing)
- **Path handling**: `helpers/path_detector.py` (cross-platform paths)
- **Docker commands**: `helpers/docker_manager.py` (command building)
- **Update system**: `daily-update-manager.sh` (security updates)

## Version History

- **Latest (2025-05-29)**: Multi-stage optimized build with intelligent caching
- **Image Size**: 1.02GB (35.4% reduction)
- **Build Time**: ~1.1 minutes (56% improvement)
- **Security**: 7+ CVEs addressed with auto-update system

## Resources

- **Docker Hub**: https://hub.docker.com/r/spd109/devops-uat
- **Repository**: (Current repository)
- **Issues**: GitHub Issues (if applicable)
- **Documentation**: README.md for user guide

---

**Last Updated**: 2025-05-29 (Based on repository state at analysis time)

**Maintained By**: DevOps Security Team

**AI Assistant Note**: This guide is specifically designed to help AI assistants understand the codebase architecture, conventions, and workflows. When in doubt, refer to existing code patterns and maintain consistency with established conventions.
