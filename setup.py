#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
import sys
from setuptools import setup, find_packages

# Define package metadata
PACKAGE_NAME = "jitsi-py"
PACKAGE_DESCRIPTION = "Python integration for Jitsi Meet video conferencing"
PACKAGE_URL = "https://github.com/Kabhishek18/jitsi-plugin"
AUTHOR = "Kumar Abhishek"
AUTHOR_EMAIL = "developer@kabhishek18.com"
LICENSE = "MIT"

# Python version check
if sys.version_info < (3, 8):
    sys.exit("ERROR: jitsi-py requires Python 3.8 or later")

# Extract version from version.py
with open("jitsi_py/version.py", "r", encoding="utf-8") as f:
    version_file = f.read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        VERSION = version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string in jitsi_py/version.py.")

# Read long description from README.md
try:
    with open("README.md", "r", encoding="utf-8") as f:
        LONG_DESCRIPTION = f.read()
except FileNotFoundError:
    LONG_DESCRIPTION = PACKAGE_DESCRIPTION

# Core dependencies
INSTALL_REQUIRES = [
    "requests>=2.25.0",    # HTTP requests
    "pyjwt>=2.0.0",        # JWT token handling
    "websocket-client>=1.0.0",  # WebSocket support
    "pyyaml>=5.1.0",       # YAML configuration
]

# Optional dependencies
EXTRAS_REQUIRE = {
    # Framework integrations
    "django": ["django>=3.0.0"],
    "flask": ["flask>=2.0.0"],
    "fastapi": ["fastapi>=0.70.0", "uvicorn>=0.15.0"],
    
    # Storage options
    "aws": ["boto3>=1.17.0"],
    
    # AI features
    "ai": ["openai>=0.27.0", "whisper>=1.0.0"],
    
    # Development and testing
    "dev": [
        "pytest>=6.0.0",
        "pytest-cov>=2.12.0",
        "pytest-mock>=3.6.0",
        "requests-mock>=1.9.0",
        "black>=21.5b2",
        "flake8>=3.9.0",
        "mypy>=0.812",
    ],
    
    # Documentation
    "docs": [
        "sphinx>=4.0.0",
        "sphinx-rtd-theme>=0.5.0",
        "sphinx-autoapi>=1.8.0",
    ],
}

# Create an "all" extra that installs all optional dependencies except dev tools
EXTRAS_REQUIRE["all"] = [
    package for name, packages in EXTRAS_REQUIRE.items() 
    if name not in ["dev", "docs"] for package in packages
]

# Package data and entry points
setup(
    name=PACKAGE_NAME,
    version=VERSION,
    description=PACKAGE_DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=PACKAGE_URL,
    packages=find_packages(),
    include_package_data=True,
    python_requires='>=3.8',
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9", 
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Communications :: Conferencing",
        "Topic :: Multimedia :: Video",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Operating System :: OS Independent",
        "Framework :: Django",
        "Framework :: Flask",
        "Framework :: FastAPI",
    ],
    keywords="jitsi,video conference,webrtc,meetings,video chat,real-time communication",
    entry_points={
        "console_scripts": [
            "jitsi-py=jitsi_py.utils.cli:main",
        ],
    },
    project_urls={
        "Documentation": f"{PACKAGE_URL}/docs",
        "Source": PACKAGE_URL,
        "Tracker": f"{PACKAGE_URL}/issues",
    },
    zip_safe=False,
)