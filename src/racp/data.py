import os
import racp.crawl as crawl
from racp.utils import save_json

class PaperItem:
    '''A structure that store data of a paper.
    
    Attributes:
       arxiv_id: The arXiv id of the paper.
       ss_id: The semantics scholar id of the paper.
       citations: Set of ss_ids of the papers cite this paper.
       references: Set of ss_ids of the papers cited by this paper.
       authors: List of semantics scholar author data of this paper.
       publication: The publication type of the paper(A list).
       date: The publication date from arXiv.
       title: The title of the paper from arXiv.
       abstract: The abstract of this paper from arXiv.
       content: The text of this paper from arXiv.
       logger: logurus logger
    '''
    def __init__(
        self,
        arxiv_id = None,
        ss_id = None,
        logger = crawl.logger
    ) -> None:
        '''Initialize with arxiv id or ss id'''
        if arxiv_id == None and ss_id == None:
            raise ValueError("You should pass a arXiv id or a semantics scholar id")
        elif arxiv_id != None:
            data = crawl.get_ss_data_by_arxiv([arxiv_id], logger)
        else:
            data = crawl.get_ss_data_by_ss([ss_id], logger)
        if data == None:
            return 
        self.arxiv_id = arxiv_id
        self.ss_id = data[0]["paperId"]
        self.citations = set([item["paperId"] for item in data[0]["citations"]])
        self.references = set([item["paperId"] for item in data[0]["references"]])
        self.authors = crawl.get_author_info([item["authorId"] for item in data[0]["authors"]], logger=logger)
        if self.authors == None:
            return
        self.publication = data[0]["publicationTypes"]
        arxiv_data = crawl.get_arxiv_data(self.arxiv_id, logger)
        if arxiv_data == None:
            return 
        self.date = arxiv_data["Published"]
        self.title = arxiv_data["Title"]
        self.abstract = arxiv_data["Summary"]
        self.content = arxiv_data["Content"]
        self.logger = logger
    
    def to_json(self):
        '''Convert to json format'''
        return {
            "arxivId": self.arxiv_id,
            "paperId": self.ss_id,
            "citations": list(self.citations),
            "references": list(self.references),
            "authors": self.authors,
            "publication": self.publication,
            "date": self.date,
            "title": self.title,
            "abstract": self.abstract,
            "content": self.content
        }
    
    def save_json(self, save_path):
        '''Save as a json file'''
        save_json(self.to_json(),os.path.join(save_path, f"{self.arxiv_id}.json"),self.logger, f"{self.arxiv_id}.json")
    

    def load_json(self, json_data):
        '''Load from a json dictionary'''
        if not isinstance(json_data, dict):
            raise ValueError("Please pass in a dictionary")
        try:
            self.arxiv_id = json_data["arxivId"]
            self.ss_id = json_data["paperId"]
            self.citations = set(json_data["citations"])
            self.references = set(json_data["references"])
            self.authors =  json_data["authors"]
            self.publication = json_data["publication"]
            self.date = json_data["date"]
            self.title = json_data["title"]
            self.abstract = json_data["abstract"]
            self.content = json_data["content"]
        except:
            raise ValueError("Fail to load data, please check the items.")
        
