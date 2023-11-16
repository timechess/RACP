from crawl import PaperCrawler
from utils import makedir
import argparse
import json
import threading
import os
import time

def parser():
    parser = argparse.ArgumentParser("Script for crawling from arxiv")
    parser.add_argument("--field", type=str, default="cs.IR", help="Field to crawl")
    parser.add_argument("--use-cache-links", default=False, action="store_true", help="use links from cached data")
    parser.add_argument("--only-links", default=False, action="store_true", help="only get pdf links")
    parser.add_argument("--threads", type=int, default=4, help="Threads used to download pdfs")
    parser.add_argument("--save-path", required=True, help="Directory to store data")

    return parser.parse_args()

arg = parser()
makedir(arg.save_path)
crawler = PaperCrawler(arg.field, 3, arg.save_path)

def download_worker(split, id):
    crawler.download(split[id])

def monitor_and_parse():
    folder_path = os.path.join(arg.save_path, "pdf")
    parsed_file = set()
    while True:
        files = os.listdir(folder_path)
        for file in files:
            if file not in parsed_file:
                file_path = os.path.join(folder_path, file)
                initial_size = os.path.getsize(file_path)
                time.sleep(2)  
                final_size = os.path.getsize(file_path)
                if initial_size == final_size:
                    try:
                        crawler.parse(file)
                        parsed_file.add(file)
                    except:
                        time.sleep(2)
                        continue
        time.sleep(2)

if __name__ == "__main__":
    if arg.only_links:
        links = crawler.get_links()
        crawler.save_json(links, os.path.join(crawler.save_path, "pdflinks.json"), "pdflinks.json")
    
    if arg.use_cache_links:
        try:
            with open(os.path.join(arg.save_path, "pdflinks.json"),"r") as f:
                pdflinks = json.load(f)
        except:
            raise ValueError(f"pdflinks.json not exists in {arg.save_path}")
    else:
        pdflinks = crawler.get_links()

    num = len(pdflinks)//arg.threads
    pdflink_split = [pdflinks[num*i:num*(i+1)] for i in range(arg.threads)]
    if len(pdflinks)-num*arg.threads != 0:
        pdflink_split[-1] += pdflinks[-(len(pdflinks)-num*arg.threads):]
    threads = []
    for i in range(arg.threads):
        t = threading.Thread(target=download_worker,args=(pdflink_split, i))
        t.start()
        threads.append(t)

    pdf_path = os.path.join(arg.save_path,"pdf")
    monitor_thread = threading.Thread(target=monitor_and_parse)
    monitor_thread.start()

    for t in threads:
        t.join()

    monitor_thread.join()