"""
Cassandra Code Analyzer - Setup Configuration
"""
from setuptools import setup, find_packages

with open("README_CASSANDRA.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cassandra-analyzer",
    version="0.1.0",
    author="Cassandra Analysis Team",
    description="Static code analyzer for Cassandra-related Java code",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/cassandra-analyzer",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.11",
    install_requires=[
        "javalang>=0.13.0",
        "jinja2>=3.1.0",
        "pyyaml>=6.0",
        "click>=8.0",
        "rich>=13.0",
    ],
    entry_points={
        "console_scripts": [
            "cassandra-analyzer=cassandra_analyzer.main:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "cassandra_analyzer": ["templates/*.html"],
    },
)
