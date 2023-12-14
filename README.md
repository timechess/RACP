# README

## Setup

To start using this project, first you should run the setup script. You can either run
```shell
pip install racp
```

or

```shell
python setup.py install
```

at the project root directory. This allows you to import `racp` in python code.

Our docs can be viewed on https://racp.readthedocs.io/en/latest/.

If you want to build the docs locally, you need to install `mkdocs`. Run these commands:
```shell
pip install mkdocs mkdocs-include-markdown-plugin mkdocstrings mkdocstrings-python
```

If you want to view the docs, run `mkdocs build` at the project root directory. It will create `./site` directory which contains `index.html` file. Open the file with your browser and read the docs.

You can run the scripts in `example` to test installation.
