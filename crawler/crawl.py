# This file implements PaperCrawler, which crawl pdfs from the Internet, parse them and save data
# into specified directory. 
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import json
import os
import time
import fitz
from utils import makedir, tokenize, save_json


def get_links(years, field, save_path, logger, headers=None, timeout=10):
    '''Get pdf links from specified field and years'''
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
            pass
    
    save_json(links, os.path.join(save_path, "pdflinks.json"), logger, "pdflinks.json")
    return links
    
def parse_pdf(filename, save_path, logger):
    '''Parse pdf to and save data'''
    file_path = os.path.join(save_path,"pdf", filename)
    try:
        pdf = fitz.open(file_path)
    except:
        logger.error(f"Broken file {filename}")
        os.remove(file_path)
        return
    text = ""
    for i in range(pdf.page_count):
        text += pdf[i].get_text()
    text = text.replace("\n"," ")
    tokens = tokenize(text)
    data = {
        "file" : filename,
        "raw" : text,
        "tokens" : tokens,
    }
    savepath = makedir(os.path.join(save_path,"parsed_data"),logger)
    save_json(data, os.path.join(savepath, os.path.splitext(filename)[0]+".json"),logger, f"{filename} parsed data")


def download(pdflinks, save_path, logger, headers=None):
    '''Download pdf and abstract from the given list of links'''
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
            logger.debug(f"【{count}/{len(pdflinks)}】Successfully write {pdf_id}.pdf")
            
        except:
            logger.error(f"Fail to download {pdf_id}.pdf")
        abs_url = f"https://arxiv.org/abs/{pdf_id}"
        try:
            res = requests.get(abs_url, headers=headers)
            res.raise_for_status()
            abs_bs = BeautifulSoup(res.text, "xml")
            abstract = abs_bs.find_all("blockquote")[0].text
            with open(os.path.join(dir_path, pdf_id+".txt"), "w", encoding="utf-8") as f:
                f.write(abstract)
        except:
            logger.error(f"Fail to get {pdf_id}'s abstract")
        time.sleep(2)


        
    
