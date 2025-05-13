#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
import sys
from setuptools import setup, find_packages

# Define package metadata
PACKAGE_NAME = "jitsi-plus-plugin"
PACKAGE_DESCRIPTION = "Comprehensive Python integration for Jitsi Meet with video conferencing, audio calls, broadcasting, and VOD"
PACKAGE_URL = "https://github.com/Kabhishek18/jitsi-plugin"
AUTHOR = "Kumar Abhishek"
AUTHOR_EMAIL = "developer@kabhishek18.com"
LICENSE = "MIT"

# Python version check
if sys.version_info < (3, 8):
    sys.exit("ERROR: jitsi-plus-plugin requires Python 3.8 or later")

# Extract version
VERSION = "4.2.0"  # Default version
version_file_path = os.path.join("jitsi_plus_plugin", "version.py")
if os.path.exists(version_file_path):
    with open(version_file_path, "r", encoding="utf-8") as f:
        version_file = f.read()
        version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
        if version_match:
            VERSION = version_match.group(1)

# Read long description from README.md
try:
    with open("README.md", "r", encoding="utf-8") as f:
        LONG_DESCRIPTION = f.read()
except FileNotFoundError:
    LONG_DESCRIPTION = PACKAGE_DESCRIPTION

# Core dependencies
INSTALL_REQUIRES = [
    "requests>=2.25.0",          # HTTP requests
    "pyjwt>=2.0.0",              # JWT token handling
    "websockets>=10.0",          # WebSocket support (asyncio based)
    "websocket-client>=1.0.0",   # WebSocket client (synchronous)
    "pyyaml>=6.0",               # YAML configuration
    "aiohttp>=3.7.4",            # Async HTTP client
    "asyncio>=3.4.3",            # Async support
    "jinja2>=3.0.1",             # Templating
    "flask>=2.0.1",              # Web framework for admin interface
]

# Optional dependencies
EXTRAS_REQUIRE = {
    # Framework integrations
    "django": ["django>=4.0.0"],
    "fastapi": ["fastapi>=0.70.0", "uvicorn>=0.15.0"],
    
    # Media server integrations
    "media": [
        "ffmpeg-python>=0.2.0",   # FFmpeg Python bindings
        "av>=8.0.0",              # PyAV for media processing
        "m3u8>=0.9.0",            # M3U8 playlist handling
    ],
    
    # Storage options
    "aws": ["boto3>=1.17.0"],
    "gcp": ["google-cloud-storage>=2.0.0"],
    
    # AI features
    "ai": [
        "openai>=0.27.0",         # OpenAI integration
        "whisper-timestamped>=1.0.0",  # Speech recognition
        "langchain>=0.0.139",     # Language model framework
    ],
    
    # Real-time data and scaling
    "scaling": [
        "redis>=4.0.0",           # Redis for real-time data
        "celery>=5.2.0",          # Task queue
        "kubernetes>=24.2.0",     # Kubernetes API for auto-scaling
    ],
    
    # Development and testing
    "dev": [
        "pytest>=6.0.0",
        "pytest-cov>=2.12.0",
        "pytest-mock>=3.6.0",
        "pytest-asyncio>=0.18.0",
        "requests-mock>=1.9.0",
        "black>=21.5b2",
        "flake8>=3.9.0",
        "mypy>=0.812",
        "pre-commit>=2.17.0",
    ],
    
    # Documentation
    "docs": [
        "sphinx>=4.0.0",
        "sphinx-rtd-theme>=0.5.0",
        "sphinx-autoapi>=1.8.0",
        "sphinx-markdown-tables>=0.0.15",
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
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9", 
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Communications :: Conferencing",
        "Topic :: Multimedia :: Video",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Video :: Capture",
        "Topic :: Multimedia :: Video :: Conversion",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Operating System :: OS Independent",
        "Framework :: Django",
        "Framework :: Flask",
        "Framework :: AsyncIO",
    ],
    keywords="jitsi,video conference,webrtc,meetings,video chat,real-time communication,broadcasting,vod,audio calls,whiteboard,polls",
    entry_points={
        "console_scripts": [
            "jitsi-plus=jitsi_plus_plugin.cli:main",
        ],
    },
    project_urls={
        "Documentation": f"{PACKAGE_URL}/docs",
        "Source": PACKAGE_URL,
        "Tracker": f"{PACKAGE_URL}/issues",
    },
    zip_safe=False,
)