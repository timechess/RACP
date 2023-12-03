import os
import json
from loguru import logger

logger.add(
    "log.log",
    enqueue=True,
    level="ERROR"
)

def makedir(
    path : str, 
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
        

def powerlaw_fit(
    data,
    xmin=None,
    fit_method="Likelihood"
):
    '''This function use `powerlaw` to fit the given data and returns `powerlaw.Fit` object.
    
    Args:
        data: List or array.
        xmin: The data value beyond which distributions should be fitted. 
        fit_method: "Likelihood" as default, "KS" optional.

    Returns:
        cdf: A `powerlaw.Fit` object.
    '''
    import powerlaw
    fit = powerlaw.Fit(data, xmin=xmin, fit_method=fit_method)
    return fit


def powerlaw_fit_cdf(
    data,
    xmin=None,
    fit_method="Likelihood"
):
    '''This function use `powerlaw` to fit the given data and returns cdf.
    
    

    Args:
        data: List or array.
        xmin: The data value beyond which distributions should be fitted. 
        fit_method: "Likelihood" as default, "KS" optional.

    Returns:
        cdf: A dictionary formated as {x : cdf(x)}.
    '''
    fit = powerlaw_fit(data, xmin, fit_method)
    cdf = fit.cdf()
    cdf = dict([(cdf[0][i], cdf[1][i]) for i in range(len(cdf[0]))])
    return cdf

def parse_pdf(
    pdfpath : str,
    stream=None
):
    '''Parse pdf files into raw text.
    
    Args:
        pdfpath: The path to pdf file.
        stream: If your pdf has already been read in binary mode, then use this arg.
    
    Returns:
        text: Raw text.
    '''
    import fitz
    if stream != None:
        pdf = fitz.open(stream=stream, filetype="pdf")
    else:
        pdf = fitz.open(pdfpath)
    text = ""
    for page in pdf.pages():
        text += page.get_text()
    return text


def CCBC(paperA, paperB, weight=dict()):
    """Calculate citation similarity index. 
    
    CCBC stands for co-citation and bib coupling index 
    plus direct citation as well 
    
    Args:
        paperA: PaperItem 
        paperB: PaperItem
        weight: A dict containing each paper's weight, default to 1.
    
    Returns:
        index: [0,1]
    """
    score = 0 
    # 1. direct citation relationship 
    if paperA.ss_id in paperB.citations:
        score += weight.get(paperA.arxiv_id, 1)/6
    if paperB.ss_id in paperA.citations:
        score += weight.get(paperB.arxiv_id, 1)/6
    # 2. shared citation ratio 
    cocite = paperA.citations.intersection(paperB.citations)
    alcite = paperA.citations.union(paperB.citations)
    score += weight.get(paperA.arxiv_id, 1) * weight.get(paperB.arxiv_id, 1) * \
                len(cocite) / len(alcite) / 3
    # 3. shared reference ratio 
    coref = paperA.references.intersection(paperB.references)
    alref = paperA.references.union(paperB.references)
    score += sum([weight.get(item.arxiv_id, 1) for item in coref]) / \
                sum([weight.get(item.arxiv_id, 1) for item in alref]) / 3
    
    return score  

