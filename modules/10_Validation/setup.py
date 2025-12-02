"""
Setup script for Module 10: Validation
"""

from setuptools import setup, find_packages

setup(
    name="tqp-validation",
    version="0.1.0",
    description="3QP Validation Framework - Comprehensive validation infrastructure",
    author="3QP Development Team",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies - uses only Python standard library
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
