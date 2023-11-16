import os
import nltk
from nltk.corpus import wordnet
from nltk import word_tokenize, pos_tag
from nltk.stem import WordNetLemmatizer

with open("./stop_words.txt", "r", encoding="utf-8") as f:
    STOPWORDS = list(map(lambda line: line.strip(),f.readlines()))

def makedir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Create {path}")
    return path

def get_wordnet_pos(tag):
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

def tokenize(text):
    '''Tokenization, remove stopwords, lemmatization'''
    text = text.lower()
    tokens = word_tokenize(text)
    tags = pos_tag(tokens)
    wnl = WordNetLemmatizer()
    result = []
    for tag in tags:
        wordnet_pos = get_wordnet_pos(tag[1]) or wordnet.NOUN
        lemma = wnl.lemmatize(tag[0], pos=wordnet_pos)
        if lemma not in STOPWORDS:
            result.append(lemma)
    return result