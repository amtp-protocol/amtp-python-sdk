#!/usr/bin/env python3
"""
Setup script for AMTP Python SDK
"""

from setuptools import setup, find_packages
import os
from pathlib import Path

# Read the README file
readme_path = Path(__file__).parent / "README.md"
if readme_path.exists():
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = "AMTP Python SDK for AI Agent Development"

# Read version from __init__.py
version = "1.0.0"
init_path = Path(__file__).parent / "amtp" / "__init__.py"
if init_path.exists():
    with open(init_path, "r") as f:
        for line in f:
            if line.startswith("__version__"):
                version = line.split("=")[1].strip().strip('"').strip("'")
                break

setup(
    name="amtp",
    version=version,
    author="Cong Wang",
    author_email="xiyou.wangc@gmail.com",
    description="Python SDK for building AI agents using the Agent Message Transfer Protocol (AMTP)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/amtp-protocol/amtp-python-sdk",
    project_urls={
        "Bug Tracker": "https://github.com/amtp-protocol/amtp-python-sdk/issues",
        "Documentation": "https://github.com/amtp-protocol/amtp-python-sdk/tree/main/docs",
        "Source Code": "https://github.com/amtp-protocol/amtp-python-sdk/tree/main/",
    },
    packages=find_packages(include=["amtp*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
    ],
    python_requires=">=3.8",
    install_requires=[
        "aiohttp>=3.8.0",
        "jsonschema>=4.0.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "yaml": [
            "PyYAML>=6.0.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "sphinx-autodoc-typehints>=1.23.0",
        ],
        "examples": [
            "PyYAML>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "amtp-agent=amtp.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "amtp": ["py.typed"],
    },
    zip_safe=False,
    keywords=[
        "amtp",
        "agent",
        "ai",
        "messaging",
        "protocol",
        "distributed",
        "communication",
        "workflow",
        "coordination",
    ],
)
