import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import os
import time
from racp.utils import makedir, save_json, parse_pdf

def get_links(
        years : int, 
        field : str, 
        save_path : str, 
        logger, 
        headers=None, 
        timeout=10
):
    '''Get pdf links from specified field and years
    
    Given years and field, it crawls from arXiV and get all pdf links that satisfies requirements.
    For example, get_links(3, cs.IR, ..) returns all cs.IR papers in 2021-2023 and saves data into
    the given path. The json file is named pdflinks.json. Internet errors will be logged and pass.

    Args:
        years: The num of years you want to crawl from 2023.
        field: The arXiV field of papers you want, like cs.IR, cs.CV.
        save_path: The path to save crawled data.
        logger: loguru logger.
        headers: Default to None.
        timeout: Default to 10.

    Returns:
        links: A List that contains all the pdf links needed.
    '''

    time = ["{}{:02}".format(23-i,j) for i in range(years) for j in range(1,13)]
    base_url = "https://arxiv.org/list"
    queries = list(map(lambda query: query + "?show=500",["/".join([base_url,field,time[i]]) for i in range(len(time))]))

    links = []
    for url in tqdm(queries):
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
    
    save_json(links, os.path.join(save_path, "pdflinks.json"), logger, "pdflinks.json")
    logger.info(f"Get {len(links)} pdf to crawl")
    return links


def download_pdf(
        pdflinks : list, 
        save_path : str, 
        logger, 
        parse=False,
        stopwords=None,
        sleep=1,
        headers=None
    ):
    '''Download pdf and abstract from the given list of links
    
    Given the pdf links to crawl, it download pdfs from the Internet and save them to given path.
    For example, the pdf will be saved as pdf/{id}.pdf.You can choose to parse the pdf while 
    downloading by pass parse=True. Now abstract won't be downloaded in this function. Check
    `download_abs`.

    Args:
        pdflinks: A List of links to download.
        save_path: The path to save data.
        logger: loguru logger.
        parse: Whether parse the pdf upon finishing download, default to False.
        stopwords: List of stopwords used by tokenization, default to None.
        sleep: Sleep time after finishing downloading one pdf, default to 1.
        headers: Default to None.
    '''

    dir_path = os.path.join(save_path, "pdf")
    count = 0
    for link in pdflinks:
        pdf_id = link.split("/")[-1]
        try:
            res = requests.get(link, headers=headers)
            res.raise_for_status()
            with open(os.path.join(dir_path, pdf_id+".pdf"), "wb") as f:
                f.write(res.content)
            count+=1
            logger.debug(f"Process {os.getpid()} : 【{count}/{len(pdflinks)}】Successfully write {pdf_id}.pdf")
            
        except:
            logger.error(f"Process {os.getpid()} : Fail to download {pdf_id}.pdf")
            continue
        #download_abs(pdf_id, save_path, logger)
        if parse:
            if stopwords == None:
                raise ValueError("You need to pass in valid stopwords to parse pdf")
            parse_pdf(os.path.join(dir_path,pdf_id+".pdf"), save_path, stopwords, logger)
        time.sleep(sleep)

def download_abs(
        abslinks : list,
        save_path : str,
        logger
):
    '''Get the abstract of given arXiV paper abstrack links.
    
    This function gets abstract of the given papers' links.

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
            abstract = abs_bs.find_all("blockquote")[0].text
            extra_content_index = abstract.find("\n\n\n")
            abstract = abstract[:extra_content_index]
            with open(os.path.join(save_path, "abs", pdfid+".txt"), "w", encoding="utf-8") as f:
                f.write(abstract)
            count += 1
            logger.debug(f"Process {os.getpid()} : 【{count}/{len(abslinks)}】Successfully write {pdfid}.txt")
        except:
            logger.error(f"Process {os.getpid()} : Fail to get {pdfid}'s abstract")


def check_download(
        pdflinks : list,
        save_path : str,
        logger
):
    '''Check whether all pdf have been downloaded and download fail cases.
    
    Given a List of pdf links, it will check the `pdf` directory under `save_path`. It returns the
    pdf links failed to download.

    Args:
        pdflinks: List of pdf links.
        save_path: The path to save data, which should contain a pdf directory.
        logger: loguru logger.

    Returns:
        pdf_failed_links: The links of failed pdfs.
        abs_failed_links: The links of failed abstracts.
    '''
    existing_abs = os.listdir(os.path.join(save_path, "abs"))
    existing_pdfs = os.listdir(os.path.join(save_path, "pdf"))
    pdf_failed_links = []
    abs_failed_links = []
    for link in pdflinks:
        pdfid = os.path.split(link)[-1]
        if pdfid + ".pdf" not in existing_pdfs:
            pdf_failed_links.append(pdfid)
        if pdfid + ".txt" not in existing_abs:
            abs_failed_links.append(pdfid)
    pdf_failed_links = list(map(lambda id: "https://arxiv.org/pdf/"+id, pdf_failed_links))
    abs_failed_links = list(map(lambda id: "https://arxiv.org/abs/"+id, abs_failed_links))
    logger.info(f"{len(pdf_failed_links)} pdfs are failed")
    logger.info(f"{len(abs_failed_links)} abs are failed")
    return pdf_failed_links, abs_failed_links

