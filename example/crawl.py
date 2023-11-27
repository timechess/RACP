import racp.crawl as crawl
from racp.utils import makedir
from racp.data import PaperItem
import argparse
import json
from multiprocessing import Process
import os
from loguru import logger

def parser():
    parser = argparse.ArgumentParser("Script for crawling from arXiV")
    parser.add_argument("--year", default=3, type=int, help="Years from 2023")
    parser.add_argument("--fields", default=["cs.IR"],nargs="+", type=str, help="Fields to crawl")
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
makedir(os.path.join(arg.save_path,"data"), logger)


def download_worker(split, id):
    for arxiv_id in split[id]:
        item = PaperItem(arxiv_id, logger=logger)
        try:
            item.save_json(os.path.join(arg.save_path, "data"))
        except:
            logger.error(f"{arxiv_id} fail")


if __name__ == "__main__":
    if arg.get_link:   
        pdfids = crawl.get_ids(arg.year, arg.fields, arg.save_path, logger)
    else:
        try:
            with open(os.path.join(arg.save_path, "targets.json"),"r") as f:
                pdfids = json.load(f)
        except:
            pdfids = crawl.get_ids(arg.year, arg.fields, arg.save_path, logger)

    if arg.check_download:
        pdfids = crawl.check_download(pdfids, arg.save_path, logger)
    pdfnum = len(pdfids)//arg.threads
    pdfid_split = [pdfids[pdfnum*i:pdfnum*(i+1)] for i in range(arg.threads)]
    if len(pdfids)-pdfnum*arg.threads != 0:
        pdfid_split[-1] += pdfids[-(len(pdfids)-pdfnum*arg.threads):]
    threads = []
    for i in range(arg.threads):
        t = Process(target=download_worker,args=(pdfid_split, i))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
