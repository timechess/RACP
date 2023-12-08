import os
import json
from loguru import logger
import yaml
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
    
    Note that some values not appeared in the given data will not have a cdf
    value. For example, 100 may not exist in the data, but 99 exists. We use
    the cdf of 99 as a substitute of the cdf of 100 in the returned dict. In 
    addition, the returned dict's keys don't start with 0. You can treat all
    the value less than the min of the keys as 0.
    
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
    count = min(cdf.keys())
    extra_values = {}
    last_cdf = 0
    for k, v in cdf.items():
        if k != count + 1:
            for i in range(int(count)+1, int(k)):
                extra_values[i] = last_cdf
        last_cdf = v
        count = k
    cdf.update(extra_values)
    return cdf

def parse_pdf(
    pdfpath=None,
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
        pdf = fitz.open(stream=stream.read(), filetype="pdf")
    else:
        pdf = fitz.open(pdfpath)
    text = ""
    for page in pdf.pages():
        text += page.get_text()
    return text

def ccbc(paperA,paperB):
    """Calculate citation similarity index. 
    
    CCBC stands for co-citation and bib coupling index 
    plus direct citation as well 
    
    Args:
        paperA: PaperItem 
        paperB: PaperItem
    
    Returns:
        index: [0,1]
    """
    score = 0 
    # 1. direct citation relationship 
    if paperA.ss_id in paperB.citations or \
        paperB.ss_id in paperA.citations:
            score += 0.5 
    # 2. shared citation ratio 
    cocite = paperA.citations.intersection(paperB.citations)
    alcite = paperA.citations.union(paperB.citations)
    score += len(cocite) / len(alcite)
    # 3. shared reference ratio 
    coref = paperA.references.intersection(paperB.references)
    alref = paperA.references.union(paperB.references)
    score += len(coref) / len(alref)
    
    return score / 2.5

def weighted_ccbc(paperA, paperB, weight=dict()):
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
        score += weight.get(paperA.ss_id, 1)/6
    if paperB.ss_id in paperA.citations:
        score += weight.get(paperB.ss_id, 1)/6
    # 2. shared citation ratio 
    cocite = paperA.citations.intersection(paperB.citations)
    alcite = paperA.citations.union(paperB.citations)
    if len(cocite) != 0:
        score += weight.get(paperA.ss_id, 1) * weight.get(paperB.ss_id, 1) * \
                    len(cocite) / len(alcite) / 3
    # 3. shared reference ratio 
    coref = paperA.references.intersection(paperB.references)
    alref = paperA.references.union(paperB.references)
    if len(coref) != 0:
        score += sum([weight.get(ss_id, 1) for ss_id in coref]) / \
                    sum([weight.get(ss_id, 1) for ss_id in alref]) / 3
    
    return score  

def arxivid2link(arxivid):
    """convert arxiv id to arxiv link 

    Args:
        arxivid (str): arxiv id 

    Returns:
        link (str)
    """
    return f'<a href="https://arxiv.org/abs/{arxivid}">{arxivid}</a>'
    # return f"https://arxiv.org/abs/{arxivid}"
class ConfigObject:
    def __init__(self, config_dict):
        self.__dict__.update(config_dict)

def load_config(config_path: str) -> ConfigObject:
    """Load configuration from a YAML file.
    
    Args:
        config_path (str): path to the YAML configuration file.
        
    Returns:
        ConfigObject: a ConfigObject instance containing the configuration data.
        
    Raises:
        FileNotFoundError: if the configuration file is not found.
        yaml.YAMLError: if the configuration file is not valid YAML.
    """
    with open(config_path, 'r') as config_file:
        config_data = yaml.safe_load(config_file)

    if config_data is not None:
        return ConfigObject(config_data)
    else:
        raise ValueError("Failed to load configuration data")
