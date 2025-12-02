"""
Setup configuration for the BDI Cognitive Cycle module.
"""

from setuptools import setup, find_packages

setup(
    name="bdi-cycle",
    version="1.0.0",
    description="BDI Cognitive Cycle module for 3QP behavioral twin system",
    author="3QP Development Team",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        # No external dependencies for core BDI module
        # Integration with TQP Core will be handled separately
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
