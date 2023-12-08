from setuptools import setup, find_packages

setup(
    name = "racp",
    version = "0.0.0",
    install_requires = [
        "requests",
        "PyMuPDF",
        "beautifulsoup4",
        "tqdm",
        "loguru",
        "nltk",
        "lxml",
        "arxiv",
        "langchain",
        "langchain_core",
        "torch==2.1.1+cu118",
        "powerlaw",
        "jsonlines",
        "sentence_transformers",
        "chromadb"
    ],
    python_requires = ">=3.8",
    packages = ["racp"],
    package_dir = {"":"src"}
)