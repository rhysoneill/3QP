"""Setup script for Intervention Engine module."""

from setuptools import setup, find_packages

setup(
    name="intervention_engine",
    version="1.0.0",
    description="Intervention Engine for 3QP System - Pure structural intervention lifecycle management",
    author="3QP Team",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies - pure Python implementation
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
