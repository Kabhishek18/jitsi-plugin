# setup.py

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="jitsi-py",
    version="0.1.0",
    description="Python integration for Jitsi Meet",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/jitsi-py",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    install_requires=[
        "requests>=2.25.0",
        "pyjwt>=2.0.0",
        "websocket-client>=1.0.0",
        "pyyaml>=5.1.0",
    ],
    extras_require={
        "django": ["django>=3.0.0"],
        "flask": ["flask>=2.0.0"],
        "fastapi": ["fastapi>=0.70.0", "uvicorn>=0.15.0"],
        "aws": ["boto3>=1.17.0"],
        "ai": ["openai>=0.27.0", "whisper>=1.0.0"],
    },
    entry_points={
        "console_scripts": [
            "jitsi-py=jitsi_py.utils.cli:main",
        ],
    },
)