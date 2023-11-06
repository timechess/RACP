# This file implements PaperCrawler, which crawl pdfs from the Internet, parse them and save data
# into specified directory. 
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import json
import os

class PaperCrawler:
    def __init__(self, field, years, save_path) -> None:
        self.field = field
        self.years = years
        self.save_path = save_path

    def get_links(self, header=None, timeout=10):
        time = ["{}{:02}".format(23-i,j) for i in range(self.years) for j in range(1,13)]
        max_entries = 1000
        base_url = "https://arxiv.org/list"
        queries = list(map(lambda query: query + "?show=500",["/".join([base_url,self.field,time[i]]) for i in range(len(time))]))

        links = []
        for url in tqdm(queries):
            try:
                res = requests.get(url, headers=header, timeout=timeout)
                res.raise_for_status()
                bs = BeautifulSoup(res.text, features="xml")
                pdf_links = bs.find_all('a', title="Download PDF")
                for link in pdf_links:
                    links.append("https://arxiv.org" + link['href'])
            except:
                pass
        
        self.save_json(links, os.path.join(self.save_path, "pdflinks.json"), "pdflinks.json")
    
    def parse(self):
        pass

    def save_json(self, obj, path, name=None):
        print(f"Saving {name} to {path}")
        with open(path, "w") as f:
            json.dump(obj, f)