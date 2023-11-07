from crawl import PaperCrawler
from utils import makedir
import argparse
import json
import threading
import os

def parser():
    parser = argparse.ArgumentParser("Script for crawling from arxiv")
    parser.add_argument("--only-links", default=False, action="store_true", help="only get pdf links")
    parser.add_argument("--only-download", default=False, action="store_true",help="only download pdf files")
    parser.add_argument("--only-parse", default=False, action="store_true", help="only parse downloaded pdf files")
    parser.add_argument("--threads", type=int, default=4, help="Threads used to download pdfs")
    parser.add_argument("--save-path", required=True, help="Directory to store data")

    return parser.parse_args()

arg = parser()
makedir(arg.save_path)
crawler = PaperCrawler("cs.IR", 3, arg.save_path)

def download_worker(split, id):
    crawler.download(split[id])


if __name__ == "__main__":
    if arg.only_links:
        crawler.get_links()

    if arg.only_download:
        try:
            with open(os.path.join(arg.save_path, "pdflinks.json"),"r") as f:
                pdflinks = json.load(f)
        except:
            raise ValueError(f"pdflinks.json not exists in {arg.save_path}")
        num = len(pdflinks)//arg.threads
        pdflink_split = [pdflinks[num*i:num*(i+1)] for i in range(arg.threads)]
        if len(pdflinks)-num*arg.threads != 0:
            pdflink_split[-1] += pdflinks[-(len(pdflinks)-num*arg.threads):]
        threads = []
        for i in range(arg.threads):
            t = threading.Thread(target=download_worker,args=(pdflink_split, i))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    if arg.only_parse:
        pdf_dir_path = os.path.join(arg.save_path,"pdf")
        pdfs = os.listdir(pdf_dir_path)
        for pdf in pdfs:
            crawler.parse(pdf)
