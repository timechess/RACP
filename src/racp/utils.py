import os
import json
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
        
    
def CCBC(paperA,paperB):
    """Calculate citation similarity index. 
    
    CCBC stands for co-citation and bib coupling index 
    plus direct citation as well 
    
    Args:
        paperA: PaperItem 
        paperB: PaperItem
    
    Returns:
        index: [0,1.5]
    """
    score = 0 
    # 1. direct citation relationship 
    if paperA.paperId in paperB.citations or \
        paperB.paperId in paperA.citations:
            score += 0.5 
    # 2. shared citation ratio 
    cocite = paperA.citations and  paperB.citations
    alcite = paperA.citations or   paperB.citations
    score += len(cocite) / len(alcite)
    # 3. shared reference ratio 
    coref = paperA.references and  paperB.references
    alref = paperA.references or   paperB.references
    score += len(coref) / len(alref)
    
    return score  

