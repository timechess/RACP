import crawl
from utils import makedir
import argparse
import json
from multiprocessing import Process
import os
from loguru import logger

logger.add(
    "log.log",
    enqueue=True,
    level="ERROR"
)

def parser():
    parser = argparse.ArgumentParser("Script for crawling from arxiv")
    parser.add_argument("--field", type=str, default="cs.IR", help="Field to crawl")
    parser.add_argument("--use-cache-links", default=False, action="store_true", help="use links from cached data")
    parser.add_argument("--only-links", default=False, action="store_true", help="only get pdf links")
    parser.add_argument("--threads", type=int, default=4, help="Threads used to download pdfs")
    parser.add_argument("--save-path", required=True, help="Directory to store data")

    return parser.parse_args()

arg = parser()
makedir(arg.save_path, logger)
makedir(os.path.join(arg.save_path, "pdf"), logger)
makedir(os.path.join(arg.save_path,"abs"), logger)


def download_worker(split, id):
    crawl.download(split[id],arg.save_path,logger)

if __name__ == "__main__":

    if arg.only_links:
        links = crawl.get_links(3, arg.field, arg.save_path, logger)
        crawl.save_json(links, os.path.join(arg.save_path, "pdflinks.json"), logger, "pdflinks.json")
        exit()

    if arg.use_cache_links:
        try:
            with open(os.path.join(arg.save_path, "pdflinks.json"),"r") as f:
                pdflinks = json.load(f)
        except:
            raise ValueError(f"pdflinks.json not exists in {arg.save_path}")
    else:
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
