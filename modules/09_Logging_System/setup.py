"""
Setup configuration for 3QP Logging System module.
"""

from setuptools import setup, find_packages

setup(
    name="tqp-logging-system",
    version="1.0.0",
    description="Unified logging infrastructure for 3QP simulation",
    author="3QP Team",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        # No external dependencies beyond Python stdlib
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
