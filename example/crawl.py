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
    parser.add_argument("--check-download", default=False, action="store_true", help="Whether only check download")
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


def pdf_download_worker(split, id):
    crawl.download_pdf(split[id],arg.save_path,logger,False, stopwords)

def abs_download_worker(split, id):
    crawl.download_abs(split[id],arg.save_path,logger)


if __name__ == "__main__":
    if arg.get_link:   
        pdflinks = crawl.get_links(3, arg.field, arg.save_path, logger)
    else:
        try:
            with open(os.path.join(arg.save_path, "pdflinks.json"),"r") as f:
                pdflinks = json.load(f)
        except:
            pdflinks = crawl.get_links(3, arg.field, arg.save_path, logger)
    if arg.check_download:
        pdflinks, abslinks = crawl.check_download(pdflinks, arg.save_path, logger)
    pdfnum = len(pdflinks)//arg.threads
    absnum = len(abslinks)//arg.threads
    pdflink_split = [pdflinks[pdfnum*i:pdfnum*(i+1)] for i in range(arg.threads)]
    abslink_split = [abslinks[absnum*i:absnum*(i+1)] for i in range(arg.threads)]
    if len(pdflinks)-pdfnum*arg.threads != 0:
        pdflink_split[-1] += pdflinks[-(len(pdflinks)-pdfnum*arg.threads):]
    if len(abslinks)-absnum*arg.threads != 0:
        abslink_split[-1] += abslinks[-(len(abslinks)-absnum*arg.threads):]
    threads = []
    for i in range(arg.threads):
        t = Process(target=abs_download_worker,args=(abslink_split, i))
        t.start()
        threads.append(t)
    for i in range(arg.threads):
        t = Process(target=pdf_download_worker,args=(pdflink_split, i))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
