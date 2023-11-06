from crawl import PaperCrawler
from utils import makedir
import argparse
import json
import os

def parser():
    parser = argparse.ArgumentParser("Script for crawling from arxiv")
    parser.add_argument("--only-links", default=False, action="store_true", help="only get pdf links")
    parser.add_argument("--only-download", default=False, action="store_true",help="only download pdf files")
    parser.add_argument("--save-path", required=True, help="Directory to store data")

    return parser.parse_args()

arg = parser()

def main():

    makedir(arg.save_path)
    crawler = PaperCrawler("cs.IR", 3, arg.save_path)
    if arg.only_links:
        crawler.get_links()

    if arg.only_download:
        try:
            with open(os.path.join(arg.save_path, "pdflinks.json"),"r") as f:
                pdflinks = json.load(f)
        except:
            raise ValueError(f"pdflinks.json not exists in {arg.save_path}")
        crawler.download(pdflinks)

if __name__ == "__main__":
    main()