import os
import json
import fitz
import re
from nltk.corpus import wordnet
from nltk import word_tokenize, pos_tag
from nltk.stem import WordNetLemmatizer

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


def pdf2text(
        pdfpath : str,
        logger,
        tolower : bool = True
):
    '''Get raw text from pdf.
    
    Args:
        pdfpath: The path of the pdf file.
        logger: loguru logger.
        tolower: Whether make all the character to lower case. Default to True.

    Returns:
        text: Raw text string.
    '''

    try:
        pdf = fitz.open(pdfpath)
    except:
        logger.error(f"Process {os.getpid()} : Unable to open {pdfpath}")
        return
    text = ""
    for i in range(pdf.page_count):
        text += pdf[i].get_text()
    
    if tolower:
        text = text.lower()
    return text


def find_ref_index(
        text : str
):
    """Find the index of the last references/reference/bibliography in the given text.

    To remove references in the raw text, this is a method to find the last title word's index.
    We will remove the content after this index in the next processing step.

    Args:
        text: The raw text string.

    Returns:
        index: The last references/reference/bibliography in the string. If there isn't any, return -1.
    """
    if "references" in text:
        indexs = [substr.start() for substr in re.finditer("references", text)]
    elif "reference" in text:
        indexs = [substr.start() for substr in re.finditer("reference", text)]
    elif "bibliography" in text:
        indexs = [substr.start() for substr in re.finditer("bibliography", text)]
    else:
        return -1
    return indexs[-1]

def parse_pdf(
        filepath : str, 
        save_path : str, 
        stopwords : list,
        logger
    ):
    '''Parse pdf to and save data
    
    Given the path of the pdf you want to parse, it saves parsed data to given path
    and name it {pdf_id}.json. If the file is broken, the error will be logged. This
    function removes references in pdf. If no references found, the file would be ignored.

    Args:
        filename: The path of pdf file you want to parse.
        save_path: The path to save parsed data.
        stopwords: List of stopwords used by tokenizaiton.
        logger: loguru logger

    Returns:
        data: A Dict contains parsed data include "file", "raw", "tokens".
    '''
    
    text = pdf2text(filepath)
    text = text.replace("\n"," ")
    ref_index = find_ref_index(text)
    if ref_index == -1:
        logger.debug(f"No reference found in {filepath}, treat it as trash")
        return None
    text = text[:ref_index]
    tokens = tokenize(text, stopwords)
    data = {
        "file" : filepath,
        "raw" : text,
        "tokens" : tokens,
    }
    savepath = makedir(os.path.join(save_path,"parsed_data"),logger)
    save_json(data, os.path.join(savepath, os.path.splitext(os.path.split(filepath)[-1])[0]+".json"),logger, f"{filepath} parsed data")
    return data