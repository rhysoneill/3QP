"""
Setup script for the Social Network module.
"""

from setuptools import setup, find_packages

setup(
    name="social_network",
    version="1.0.0",
    description="Social Network & Clique Formation module for 3QP system",
    author="3QP Project",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.20.0",
    ],
    python_requires=">=3.8",
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
