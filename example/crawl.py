import racp.crawl as crawl
from racp.utils import makedir
import argparse
import json
from multiprocessing import Process
import os
from loguru import logger

with open("resources\stop_words.txt", "r", encoding="utf-8") as f:
    stopwords = list(map(lambda word: word.strip(), f.readlines()))

def parser():
    parser = argparse.ArgumentParser("Script for crawling from arXiV")
    parser.add_argument("--field", type=str, default="cs.IR", help="Field to crawl")
    parser.add_argument("--get-link", default=False, action="store_true", help="Get pdf links and save")
    parser.add_argument("--threads", type=int, default=4, help="Threads used to download pdfs")
    parser.add_argument("--save-path", default="./data", help="Directory to store data")

    return parser.parse_args()

arg = parser()

logger.add(
    os.path.join(arg.save_path,"log.log"),
    enqueue=True,
    level="ERROR"
)

makedir(arg.save_path, logger)
makedir(os.path.join(arg.save_path, "pdf"), logger)
makedir(os.path.join(arg.save_path,"abs"), logger)


def download_worker(split, id):
    crawl.download(split[id],arg.save_path,logger,True, stopwords)

if __name__ == "__main__":
    if arg.get_link:   
        pdflinks = crawl.get_links(3, arg.field, arg.save_path, logger)
    else:
        try:
            with open(os.path.join(arg.save_path, "pdflinks.json"),"r") as f:
                pdflinks = json.load(f)
        except:
            pdflinks = crawl.get_links(3, arg.field, arg.save_path, logger)
        
    num = len(pdflinks)//arg.threads
    pdflink_split = [pdflinks[num*i:num*(i+1)] for i in range(arg.threads)]
    if len(pdflinks)-num*arg.threads != 0:
        pdflink_split[-1] += pdflinks[-(len(pdflinks)-num*arg.threads):]
    threads = []
    for i in range(arg.threads):
        t = Process(target=download_worker,args=(pdflink_split, i))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()