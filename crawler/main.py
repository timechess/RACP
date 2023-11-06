from crawl import PaperCrawler
import argparse
import os

def parser():
    parser = argparse.ArgumentParser("Script for crawling from arxiv")
    parser.add_argument("--only-links", default=False, action="store_true", help="only get pdf links")
    parser.add_argument("--save-path", required=True, help="Directory to store data")

    return parser.parse_args()

arg = parser()

def main():
    if not os.path.exists(arg.save_path):
        os.makedirs(arg.save_path)
        
    if arg.only_links:
        crawler = PaperCrawler("cs.IR", 3, arg.save_path)
        crawler.get_links()

if __name__ == "__main__":
    main()