#!/usr/bin/env python3
"""
Setup script for DevOps Universal Scanner
Pure Python 3.13 Engine
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="devops-universal-scanner",
    version="3.0.0",
    description="Multi-cloud Infrastructure as Code security scanner with native intelligence",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="DevOps Security Team",
    author_email="devops@example.com",
    url="https://github.com/resolve109/devops-universal-scanner",
    license="MIT",

    packages=find_packages(include=["core", "core.*", "analyzers", "analyzers.*", "helpers", "helpers.*"]),

    python_requires=">=3.13",

    install_requires=[
        "checkov>=3.2.0",
        "cfn-lint>=1.0.0",
        "pycfmodel>=0.22.0",
        "boto3>=1.35.0",
        "botocore>=1.35.0",
        "azure-mgmt-compute>=30.0.0",
        "google-cloud-billing>=1.12.0",
        "pyyaml>=6.0.1",
        "python-hcl2>=4.3.0",
        "jinja2>=3.1.0",
        "packaging>=24.0",
        "requests>=2.32.0",
        "tabulate>=0.9.0",
        "jsonschema>=4.0.0",
        "psutil>=6.0.0",
        "bandit>=1.7.0",
        "safety>=3.0.0",
        "setuptools>=75.0.0",
        "wheel>=0.43.0",
    ],

    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=4.0.0",
            "black>=24.0.0",
            "ruff>=0.3.0",
        ],
    },

    entry_points={
        "console_scripts": [
            "devops-scan=cli:main",
        ],
    },

    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.13",
        "Topic :: Security",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: System :: Systems Administration",
    ],

    keywords="security scanning iac terraform cloudformation kubernetes docker azure gcp aws devops finops",

    project_urls={
        "Bug Reports": "https://github.com/resolve109/devops-universal-scanner/issues",
        "Source": "https://github.com/resolve109/devops-universal-scanner",
    },
)
