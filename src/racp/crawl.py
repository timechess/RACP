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


def download_pdf(
        pdflinks : list, 
        save_path : str, 
        logger=logger, 
    ):
    '''Aborted, don't use.
    
    Given the pdf links to crawl, it download pdfs from the Internet and save them to given path.
    For example, the pdf will be saved as pdf/{id}.pdf. Now abstract won't be downloaded in this 
    function. Check `download_abs`.

    Args:
        pdflinks: A List of links to download.
        save_path: The path to save data.
        logger: loguru logger.
    '''

    dir_path = os.path.join(save_path, "pdf")
    count = 0
    for link in pdflinks:
        pdf_id = link.split("/")[-1]
        try:
            res = requests.get(link)
            res.raise_for_status()
            with open(os.path.join(dir_path, pdf_id+".pdf"), "wb") as f:
                f.write(res.content)
            count+=1
            logger.debug(f"Process {os.getpid()} : 【{count}/{len(pdflinks)}】Successfully write {pdf_id}.pdf")
            
        except:
            logger.error(f"Process {os.getpid()} : Fail to download {pdf_id}.pdf")
            continue
        #download_abs(pdf_id, save_path, logger)

def download_abs(
        abslinks : list,
        save_path : str,
        logger=logger
    ):
    '''Aborted, don't use.
    
    This function gets abstract of the given papers' links. It will save to `save_path`/abs/{pdf_id}.txt.

    Args:
        abslinks: A List of links to download.
        save_path: The path to save directory.
        logger: loguru logger.
    '''
    count = 0
    for link in abslinks:
        pdfid = link.split("/")[-1]
        try:
            res = requests.get(link)
            res.raise_for_status()
            abs_bs = BeautifulSoup(res.text, "xml")
            abstract = abs_bs.find_all("blockquote")[0].text.replace("Abstract:", "")
            extra_content_index = abstract.find("\n\n\n")
            abstract = abstract[:extra_content_index]
           
            with open(os.path.join(save_path, "abs", pdfid+".txt"), "w", encoding="utf-8") as f:
                f.write(abstract)
            count += 1
            logger.debug(f"Process {os.getpid()} : 【{count}/{len(abslinks)}】Successfully write {pdfid}.txt")
        except:
            logger.error(f"Process {os.getpid()} : Fail to get {pdfid}'s abstract")

def download(
        pdfids : list,
        save_path : str,
        logger=logger
    ):
    '''Use the api from `langchain` to download data given arXiv ids.
    
    This function uses `ArxivLoader` from `langchain`. It will save metadata and raw text data into
    `save_path/data`. The pdfs won't be stored.

    Args:
        pdfids: A List of arXiV ids of the papers you want.
        save_path: The path to save data.
        logger: loguru logger.
    '''
    save_dir = makedir(os.path.join(save_path,"data"),logger)
    for pdfid in pdfids:
        try:
            document = ArxivLoader(pdfid).load()[0] 
            content = document.page_content
            data = document.metadata
            data["Content"] = content
            save_json(data, os.path.join(save_dir, f"{pdfid}.json"), logger, f"{pdfid}.json")
        except:
            logger.error(f"Fail to download {pdfid}")
    

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

