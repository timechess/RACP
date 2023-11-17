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
        "lxml"
    ],
    python_requires = ">=3.8",
    packages = ["racp"],
    package_dir = {"":"src"}
)