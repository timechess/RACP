import os
import json
import fitz
import re
from nltk.corpus import wordnet
from nltk import word_tokenize, pos_tag
from nltk.stem import WordNetLemmatizer
from loguru import logger
logger.add(
    "log.log",
    enqueue=True,
    level="ERROR"
)
def makedir(
    path : int, 
    logger
):
    '''A mkdir command that can recursively create directory and output log.
    
    Args:
        path: The path of the directory you want to create.
        logger: loguru logger
    
    Returns:
        path: The input path.
    '''

    if not os.path.exists(path):
        os.makedirs(path)
        logger.debug(f"Create {path}")
    return path

def save_json(
    obj, 
    path : str, 
    logger, 
    name=None
):
    '''A helper function to save json files.
    
    Args:
        obj: The object you want to save.
        path: The file path to save.
        logger: loguru logger.
        name: Default to None. Appear in log.
    '''

    logger.debug(f"Process {os.getpid()} : Saving {name} to {path}")
    with open(path, "w", encoding= "utf-8") as f:
        json.dump(obj, f, indent=4)

def get_wordnet_pos(tag):
    '''Helper function for tokenize'''
    if tag.startswith('J'):
        return wordnet.ADJ
    elif tag.startswith('V'):
        return wordnet.VERB
    elif tag.startswith('N'):
        return wordnet.NOUN
    elif tag.startswith('R'):
        return wordnet.ADV
    else:
        return None

def tokenize(
    text : str, 
    stopwords : list
):
    '''Tokenization, remove stopwords, lemmatization
    
    The text process function. It needs some nltk_data downloaded in advance.
    The stopwords can be downloaded from https://github.com/elephantnose/characters.

    Args:
        text: Raw text to process.
        stopwords: The List of stopwords.
    
    Returns:
        tokens: A List of tokens.
    '''
    text = text.lower()
    tokens = word_tokenize(text)
    tags = pos_tag(tokens)
    wnl = WordNetLemmatizer()
    result = []
    for tag in tags:
        wordnet_pos = get_wordnet_pos(tag[1]) or wordnet.NOUN
        lemma = wnl.lemmatize(tag[0], pos=wordnet_pos)
        if lemma not in stopwords:
            result.append(lemma)
    return result
