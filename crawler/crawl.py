# This file implements PaperCrawler, which crawl pdfs from the Internet, parse them and save data
# into specified directory. 
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import json
import os
import time
import fitz
from utils import makedir, tokenize

class PaperCrawler:
    def __init__(self, field, years, save_path) -> None:
        self.field = field
        self.years = years
        self.save_path = save_path

    def get_links(self, headers=None, timeout=10):
        '''Get pdf links from specified field and years'''
        time = ["{}{:02}".format(23-i,j) for i in range(self.years) for j in range(1,13)]
        base_url = "https://arxiv.org/list"
        queries = list(map(lambda query: query + "?show=500",["/".join([base_url,self.field,time[i]]) for i in range(len(time))]))

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
        
        self.save_json(links, os.path.join(self.save_path, "pdflinks.json"), "pdflinks.json")
        return links
    
    def parse(self, filename):
        '''Parse pdf to and save data'''
        pdf_path = os.path.join(self.save_path,"pdf", filename)
        try:
            pdf = fitz.open(pdf_path)
        except:
            print(f"Broken file {filename}")
            os.remove(pdf_path)
            return
        text = ""
        for i in range(pdf.page_count):
            text += pdf[i].get_text()
        text = text.replace("\n"," ")
        tokens = tokenize(text)
        data = {
            "file" : filename,
            "raw" : text,
            "tokens" : tokens
        }
        savepath = makedir(os.path.join(self.save_path,"parsed_data"))
        with open(os.path.join(savepath, os.path.splitext(filename)[0]+".json"), "w",encoding="utf-8") as f:
            json.dump(data, f)
        print(f"Parse {filename}")

    def download(self, pdflinks, headers=None):
        '''Download pdf from the given list of links'''
        dir_path = makedir(os.path.join(self.save_path, "pdf"))
        count = 0
        for link in pdflinks:
            pdf_id = link.split("/")[-1]
            try:
                res = requests.get(link, headers=headers)
                res.raise_for_status()
                with open(os.path.join(dir_path, pdf_id+".pdf"), "wb") as f:
                    f.write(res.content)
                count+=1
                print(f"【{count}/{len(pdflinks)}】Successfully write {pdf_id}.pdf")
                time.sleep(2)
            except:
                print(f"Fail to download {pdf_id}.pdf")

    def save_json(self, obj, path, name=None):
        print(f"Saving {name} to {path}")
        with open(path, "w") as f:
            json.dump(obj, f)
        
    
