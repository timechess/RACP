import os
from racp.crawl import get_ss_data_by_arxiv, get_ss_data_by_ss, get_arxiv_data, get_author_info, logger
from racp.utils import save_json

class PaperItem:
    '''A structure that store data of a paper.
    
    Attributes:
       arxiv_id: The arXiv id of the paper.
       ss_id: The semantics scholar id of the paper.
       citations: List of ss_ids of the papers cite this paper.
       references: List of ss_ids of the papers cited by this paper.
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
        logger = logger
    ) -> None:
        '''Initialize with arxiv id or ss id'''
        if arxiv_id == None and ss_id == None:
            raise ValueError("You should pass a arXiv id or a semantics scholar id")
        elif arxiv_id != None:
            data = get_ss_data_by_arxiv([arxiv_id], logger)
        else:
            data = get_ss_data_by_ss([ss_id], logger)
        if data == None:
            return 
        self.arxiv_id = arxiv_id
        self.ss_id = data[0]["paperId"]
        self.citations = [item["paperId"] for item in data[0]["citations"]]
        self.references = [item["paperId"] for item in data[0]["references"]]
        self.authors = get_author_info([item["authorId"] for item in data[0]["authors"]], logger=logger)
        if self.authors == None:
            return
        self.publication = data[0]["publicationTypes"]
        arxiv_data = get_arxiv_data(self.arxiv_id, logger)
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
            "citations": self.citations,
            "references": self.references,
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
    
