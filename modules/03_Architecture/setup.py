"""
Setup configuration for Module 03: Architecture Overview
"""

from setuptools import setup, find_packages

setup(
    name="tqp-architecture",
    version="1.0.0",
    description="3QP System Architecture - Orchestration and Integration Layer",
    author="3QP Development Team",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        # No external dependencies beyond Python standard library
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
