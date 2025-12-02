"""
Setup configuration for Pattern Recognition Engine
Phase 4 / Workstream 3
"""

from setuptools import setup, find_packages

setup(
    name="pattern-recognition",
    version="0.1.0",
    description="Architecture-only pattern recognition framework for 3QP system",
    author="3QP Project",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies - pure Python architecture
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
