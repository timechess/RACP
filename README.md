# README

## Setup

To start using this project, first you should run the setup script. You can either run
```shell
pip install -e .
```

or

```shell
python setup.py install
```

at the project root directory. This allows you to import `racp` in python code.

If you want to read the docs, for now you need to install `mkdocs` yourself since we haven't deploy our docs. So you need to run these commands:
```shell
pip install mkdocs
pip install mkdocs-include-markdown-plugin
pip install mkdocstrings
pip install mkdocstrings-python
```

If you want to view the docs, run `mkdocs build` at the project root directory. It will create `./site` directory which contains `index.html` file. Open the file with your browser and read the docs.

You still need additional nltk_data to use our text processing function. Download them from https://github.com/nltk/nltk_data. For now, we need the following data:
```
corpora/wordnet
taggers/*
tokenizers/punkt
```

Download the `zip` files. Create a directory named `nltk_data` in the root directory of disk C/D/E, unzip and organize the files like:
```
D:\NLTK_DATA
├─corpora
│  ├─wordnet
├─taggers
│  ├─averaged_perceptron_tagger
│  ├─averaged_perceptron_tagger_ru
│  ├─maxent_treebank_pos_tagger
│  └─universal_tagset
└─tokenizers
    └─punkt
```

Done! Also, we recommend download stopwords from https://github.com/elephantnose/characters. And the same file is in this project's `resources` directory.

You can run the scripts in `example` to test installation.
