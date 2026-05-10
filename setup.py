"""
Setup configuration for GTFS Route Planning API
Enables pip-installable package distribution
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="gtfs-route-planning-api",
    version="1.0.0",
    author="GTFS Project",
    description="FastAPI backend for GTFS spatial route planning",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/gtfs-query-portal",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP",
    ],
    python_requires=">=3.9",
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn==0.24.0",
        "psycopg2-binary==2.9.9",
        "pydantic==2.5.0",
        "python-dotenv==1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest==7.4.3",
            "pytest-asyncio==0.21.1",
            "black==23.12.0",
            "pylint==3.0.3",
        ],
        "prod": [
            "gunicorn==21.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "gtfs-api=main:app",
        ],
    },
)
