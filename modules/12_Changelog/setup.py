"""
Setup script for Changelog & Notes module.
"""

from setuptools import setup, find_packages

setup(
    name="changelog",
    version="1.0.0",
    description="Changelog & Notes: Version control and change documentation management for 3QP",
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
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Software Development :: Documentation",
        "Topic :: Software Development :: Version Control",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
