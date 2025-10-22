"""
Setup script for Whisp Assistant
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="whisp-assistant",
    version="1.0.0",
    author="Whisp Assistant Team",
    author_email="contact@whisp-assistant.com",
    description="Un assistant vocal personnel intelligent et multilingue",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/votre-username/whisp-assistant",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Shells",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "isort>=5.10.0",
            "mypy>=0.991",
            "bandit>=1.7.0",
            "safety>=2.3.0",
        ],
        "gpu": [
            "torch>=1.12.0",
            "torchaudio>=0.12.0",
            "transformers>=4.21.0",
        ],
        "web": [
            "flask>=2.2.0",
            "flask-cors>=4.0.0",
            "werkzeug>=2.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "whisp-assistant=main:assistant_vocal",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["templates/*.html", "static/css/*.css", "static/js/*.js"],
    },
    keywords=[
        "assistant",
        "voice assistant",
        "speech recognition",
        "text-to-speech",
        "automation",
        "natural language",
        "ai",
        "python",
    ],
    project_urls={
        "Bug Reports": "https://github.com/votre-username/whisp-assistant/issues",
        "Source": "https://github.com/votre-username/whisp-assistant",
        "Documentation": "https://docs.whisp-assistant.com",
        "Changelog": "https://github.com/votre-username/whisp-assistant/blob/main/CHANGELOG.md",
    },
)