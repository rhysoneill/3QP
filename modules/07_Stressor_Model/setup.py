"""
Setup script for Stressor Model module.
"""

from setuptools import setup, find_packages

setup(
    name="stressor-model",
    version="1.0.0",
    description="Lunar Mission Stressor Model: Time-varying stressor signal generation for 3QP",
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
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
