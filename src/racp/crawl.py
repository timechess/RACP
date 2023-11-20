import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import os
import json
import time
from racp.utils import save_json
from loguru import logger

logger.add(
    "log.log",
    enqueue=True,
    level="ERROR"
)

def get_links(
        years : int, 
        fields : list, 
        save_path : str,
        logger=logger, 
        headers=None, 
        timeout=30
    ):
    '''Get pdf links from specified field and years
    
    Given years and field, it crawls from arXiV and get all pdf links that satisfies requirements.
    For example, get_links(3, [cs.IR], ..) returns all cs.IR papers in 2021-2023 and saves data into
    the given path. The json file is named "pdflinks.json". Internet errors will be logged and pass.
    Note that we first need to get all urls to crawl since arXiV defaultly set one page contains 25
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
        links: A List that contains all the pdf links needed.
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
    links = []
    for url in tqdm(all_queries):
        try:
            res = requests.get(url, headers=headers, timeout=timeout)
            res.raise_for_status()
            bs = BeautifulSoup(res.text, features="xml")
            pdf_links = bs.find_all('a', title="Download PDF")
            for link in pdf_links:
                links.append("https://arxiv.org" + link['href'])
        except:
            logger.error(f"Fail to get {url}")
            pass
    links = list(set(links))
    save_json(links, os.path.join(save_path, "pdflinks.json"), logger, "pdflinks.json")
    logger.info(f"Get {len(links)} pdf to crawl")
    return links


def download_pdf(
        pdflinks : list, 
        save_path : str, 
        logger=logger, 
    ):
    '''Download pdf and abstract from the given list of links
    
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
    '''Get the abstract of given arXiV paper abstrack links.
    
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
        mode : str,
        save_path : str,
        logger=logger
    ):
    '''A joint api for pdf and abs
    
    This function uses `download_pdf` and `download_abs`. It only needs papers' arXiV ids. You can 
    specify which to download by passing the `mode` argument.

    Args:
        pdfid: A List of arXiV ids of the papers you want.
        mode: "pdf" or "abs" or "all".
        save_path: The path to save data.
        logger: loguru logger.
    '''
    pdflinks = [f"https://arxiv.org/pdf/{pdfid}" for pdfid in pdfids]
    abslinks = [f"https://arxiv.org/abs/{pdfid}" for pdfid in pdfids]
    if mode == "pdf":
        download_pdf(pdflinks, save_path, logger)
    elif mode == "abs":
        download_abs(abslinks, save_path, logger)
    elif mode == "all":
        download_pdf(pdflinks, save_path, logger)
        download_abs(abslinks, save_path, logger)
    else:
        raise ValueError("Unknown mode. Please select in ['pdf', 'abs', 'all']")
    

def check_download(
        pdfids : list,
        save_path : str,
        logger=logger
    ):
    '''Check whether all pdf have been downloaded and download fail cases.
    
    Given a List of pdf ids, it will check the `pdf` directory under `save_path`. It returns the
    pdf or abstract ids failed to download.

    Args:
        pdfids: List of pdf links.
        save_path: The path to save data, which should contain a pdf directory.
        logger: loguru logger.

    Returns:
        pdf_failed_ids: The ids of failed pdfs.
        abs_failed_ids: The ids of failed abstracts.
    '''
    existing_abs = os.listdir(os.path.join(save_path, "abs"))
    existing_pdfs = os.listdir(os.path.join(save_path, "pdf"))
    pdf_failed_ids = []
    abs_failed_ids = []
    for pdfid in pdfids:
        if pdfid + ".pdf" not in existing_pdfs:
            pdf_failed_ids.append(pdfid)
        if pdfid + ".txt" not in existing_abs:
            abs_failed_ids.append(pdfid)
    logger.info(f"{len(pdf_failed_ids)} pdfs are failed")
    logger.info(f"{len(abs_failed_ids)} abs are failed")
    return pdf_failed_ids, abs_failed_ids

