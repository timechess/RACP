import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import os
import json
import time
from racp.utils import save_json, makedir
from loguru import logger
from langchain.document_loaders import ArxivLoader

logger.add(
    "log.log",
    enqueue=True,
    level="ERROR"
)

def get_ids(
        years : int, 
        fields : list, 
        save_path : str,
        logger=logger, 
        headers=None, 
        timeout=30
):
    '''Get pdf arXiv ids from specified field and years
    
    Given years and field, it crawls from arXiV and get all pdf ids that satisfies requirements.
    For example, get_links(3, [cs.IR], ..) returns all cs.IR papers in 2021-2023 and saves data into
    the given path. The json file is named "targets.json". Internet errors will be logged and pass.
    Note that we first need to get all urls to crawl since arXiv defaultly set one page contains 25
    paper. The cache will be saved as "all_queries.json". If you want to crawl again, please delete
    the cache.

    Args:
        years: The num of years you want to crawl from 2023.
        fields: A List of arXiV fields of papers you want, like cs.IR, cs.CV.
        save_path: The path to save crawled data.
        logger: loguru logger.
        headers: Default to None.
        timeout: Default to 30.

    Returns:
        ids: A List that contains all the pdf ids needed.
    '''

    times = ["{}{:02}".format(23-i,j) for i in range(years) for j in range(1,13)]
    base_url = "https://arxiv.org/list"
    failed_cases = []
    first_queries = []
    all_queries = []
    if os.path.exists(os.path.join(save_path, "all_queries.json")):
        with open(os.path.join(save_path, "all_queries.json")) as f:
            all_queries = json.load(f)
    else:
        for field in fields:
            queries = ["/".join([base_url,field,times[i]]) for i in range(len(times))]
            first_queries += queries
        logger.debug("Start to construct all urls to crawl")
        for url in tqdm(first_queries):
            try:
                res = requests.get(url, headers=headers, timeout=timeout)
                res.raise_for_status()
                bs = BeautifulSoup(res.text, features="xml")
                paper_num = int(bs.find_all("small")[0].text.split(" ")[3])
                queries = [url + f"?skip={100*i}&show=100" for i in range(paper_num//100+1)]
                all_queries += queries
                time.sleep(5)
            except:
                logger.error(f"Fail to get {url}")
                failed_cases.append(url)
                pass
        logger.debug("Trying again to get failed cases")
        for url in tqdm(failed_cases):
            try:
                res = requests.get(url, headers=headers, timeout=timeout)
                res.raise_for_status()
                bs = BeautifulSoup(res.text, features="xml")
                paper_num = int(bs.find_all("small")[0].text.split(" ")[3])
                queries = [url + f"?skip={100*i}&show=100" for i in range(paper_num//100+1)]
                all_queries += queries
                time.sleep(5)
            except:
                logger.error(f"Fail to get {url}")
                pass
        save_json(all_queries, os.path.join(save_path, "all_queries.json"),logger, "all_queries.json")
    ids = []
    for url in tqdm(all_queries):
        try:
            res = requests.get(url, headers=headers, timeout=timeout)
            res.raise_for_status()
            bs = BeautifulSoup(res.text, features="xml")
            pdf_links = bs.find_all('a', title="Download PDF")
            for link in pdf_links:
                ids.append(link['href'].split("/")[-1])
        except:
            logger.error(f"Fail to get {url}")
            pass
    ids = list(set(ids))
    save_json(ids, os.path.join(save_path, "targets.json"), logger, "targets.json")
    logger.info(f"Get {len(ids)} pdf to crawl")
    return ids

def get_ss_data_by_arxiv(
        arxiv_ids, 
        logger=logger, 
        count=0
):
    '''Get semantics scholar data given arXiv id'''
    try:
        r = requests.post(
            'https://api.semanticscholar.org/graph/v1/paper/batch',
            params={'fields': 'externalIds,citations,publicationTypes,authors,references',},
            json={"ids": [f"ARXIV:{id}" for id in arxiv_ids]}
        )
        r.raise_for_status()
        return r.json()
    except:
        if count < 3:
            logger.warning(f"Fail {count+1} time, try again in 3 secs")
            time.sleep(3)
            return get_ss_data_by_arxiv(arxiv_ids, logger, count+1)
        else:
            logger.error(f"Failed to get {arxiv_ids} for 3 times. Give up.")
            return None
    
def get_ss_data_by_ss(
        ss_ids, 
        logger=logger, 
        count = 0
):
    '''Get semantics scholar data given ss id'''
    try:
        r = requests.post(
            'https://api.semanticscholar.org/graph/v1/paper/batch',
            params={'fields': 'externalIds,citations,publicationTypes,authors,references',},
            json={"ids": ss_ids}
        )
        r.raise_for_status()
        return r.json()
    except:
        if count < 3:
            logger.warning(f"Fail {count+1} time, try again in 3 secs")
            time.sleep(3)
            return get_ss_data_by_ss(ss_ids, logger, count+1)
        else:
            logger.error(f"Failed to get {ss_ids} for 3 times. Give up.")
            return None
        
def get_arxiv_data(
        arxiv_id : str,
        logger=logger
    ):
    '''Use the api from `langchain` to download data given arXiv ids.
    
    This function uses `ArxivLoader` from `langchain`. 

    Args:
        arxiv_id: The arXiv id of the paper you want.
        logger: loguru logger.
        
    Returns:
        data: A dictionary containing the paper's metedata and content.
    '''
    try:
        document = ArxivLoader(arxiv_id).load()[0] 
        content = document.page_content
        data = document.metadata
        data["Content"] = content
        logger.debug(f"Successfully get {arxiv_id}")
        return data
    except:
        logger.error(f"Fail to download {arxiv_id}")
        return None

def get_author_info(
        author_ids,
        logger=logger,
        count=0
):
    '''Get author data from semantics scholar'''
    try:
        r = requests.post(
            'https://api.semanticscholar.org/graph/v1/author/batch',
            params={'fields': 'name,citationCount,paperCount'},
            json={"ids": author_ids}
        )
        r.raise_for_status()
        return r.json()
    except:
        if count < 3:
            logger.warning(f"Fail {count+1} time, try again in 3 secs")
            time.sleep(3)
            get_author_info(author_ids, logger, count+1)
        else:
            logger.error(f"Failed to get {author_ids} for 3 times. Give up.")
            return None

def check_download(
        pdfids : list,
        save_path : str,
        logger=logger
    ):
    '''Check whether all pdf have been downloaded and download fail cases.
    
    Given a List of pdf ids, it will check the `data` directory under `save_path`. It returns the
    pdf ids failed to download.

    Args:
        pdfids: List of pdf ids.
        save_path: The path to save data.
        logger: loguru logger.

    Returns:
        failed_ids: The ids of failed pdfs.
    '''
    existing = os.listdir(os.path.join(save_path, "data"))
    failed_ids = []
    for pdfid in pdfids:
        if pdfid + ".json" not in existing:
            failed_ids.append(pdfid)
    logger.info(f"{len(failed_ids)} pdfs are failed")
    return failed_ids

