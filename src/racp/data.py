import os
import json
import jsonlines
from tqdm import tqdm
import racp.crawl as crawl
from racp.utils import save_json
from torch.utils.data import Dataset

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
        data = None,
        logger = crawl.logger,
        key = ""
    ) -> None:
        '''Initialize with arxiv id or ss id. Pass in an api key if you have.'''
        self.arxiv_id = ""
        self.ss_id = ""
        self.citations = set()
        self.references = set()
        self.authors = []
        self.publication = []
        self.date = ""
        self.title = ""
        self.abstract = ""
        self.content = ""
        self.logger = logger
        if arxiv_id != None:
            self.get_data_by_arxiv(arxiv_id, key)
        if data != None:
            self.load_json(data)

    def __repr__(self) -> str:
        return json.dumps(self.to_json(), indent=2)
    
    def get_data_by_arxiv(self, arxiv_id, key):
        try:
            data = crawl.get_ss_data_by_arxiv(arxiv_id, self.logger, key)
        except:
            raise ConnectionError("Fail to get semantics scholar data.")
        self.arxiv_id = arxiv_id
        self.ss_id = data["paperId"]
        self.citations = set([item["paperId"] for item in data["citations"]])
        self.references = set([item["paperId"] for item in data["references"]])
        try:
            self.authors = crawl.get_author_info([item["authorId"] \
                                                  for item in data["authors"]], self.logger, key)
        except:
            raise ConnectionError("Fail to get semantics scholar data.")
        self.publication = data["publicationTypes"]
        self.date = data["publicationDate"]
        self.title = data["title"]
        self.abstract = data["abstract"]
        try:
            self.content = crawl.get_arxiv_data(self.arxiv_id, self.logger)
        except:
            raise ConnectionError("Fail to get arXiv data.")
    
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
        
    def to_Document(self):
        from langchain_core.documents.base import Document
        data = self.to_json()
        data.pop('abstract', None)
        data.pop('content', None)
        doc = Document(metadata=data,page_content=data['content'])
        return doc 
    
    def save_json(self, save_path):
        '''Save as a json file'''
        save_json(self.to_json(),os.path.join(save_path, f"{self.arxiv_id}.json"),\
                  self.logger, f"{self.arxiv_id}.json")
    
    def load_json(self, json_data):
        '''Load from a json dictionary'''
        if not isinstance(json_data, dict):
            raise ValueError("Please pass in a dictionary")
        try:
            self.arxiv_id = json_data.get("arxivId", "")
            self.ss_id = json_data.get("paperId", "")
            self.citations = set(json_data.get("citations", []))
            self.references = set(json_data.get("references",[]))
            self.authors =  json_data.get("authors", [])
            self.publication = json_data.get("publication", [])
            self.date = json_data.get("date", "")
            self.title = json_data.get("title", "")
            self.abstract = json_data.get("abstract", "")
            self.content = json_data.get("content", "")
        except:
            raise ValueError("Fail to load data, please check the items.")
        

class RawSet(Dataset):
    '''A torch Dataset storing raw data.'''
    def __init__(self, save_path=None) -> None:
        super().__init__()
        self.items = []  # List of PaperItems
        if save_path != None:
            self._load_from_directory(save_path)

    def _load_from_directory(self, save_path):
        '''Load json files from given directory.'''
        filenames = os.listdir(save_path)
        for file in tqdm(filenames):
            path = os.path.join(save_path, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except:
                print(path)
                continue
            item = PaperItem()
            item.load_json(data)
            self.items.append(item)
    
    def add_item(self, item : PaperItem):
        self.items.append(item)
        
    def __getitem__(self, index) -> PaperItem:
        return self.items[index]
    
    def __len__(self):
        return len(self.items)
    
    def save(self, filepath):
        '''Save as jsonl file.'''
        with jsonlines.open(filepath, "w") as f:
            for item in self.items:
                data = item.to_json()
                f.write(data)
    
    def load(self, filepath):
        '''Load from a jsonl file.'''
        with jsonlines.open(filepath, "r") as f:
            for item in f:
                self.items.append(PaperItem(data=item))
    
    def all_papers(self):
        '''Return a set of semantics scholar ids involved.'''
        papers = set()
        for item in self.items:
            papers.add(item.ss_id)
            for cite in item.citations:
                papers.add(cite)
            for ref in item.references:
                papers.add(ref)
        return papers
    
    def all_authors(self):
        '''Return a dictionary with all author ids in the dataset as keys.'''
        all_authors = {}
        for item in self.items:
            try:
                for author in item.authors:
                    all_authors[author["authorId"]] = {
                        "name": author["name"],
                        "paperCount": author["paperCount"],
                        "citationCount": author["citationCount"]
                    }
            except:
                continue
        
        return all_authors
    
    def publication_types(self):
        '''Return a dictionary counting all publication types' papers.'''
        type_count = {}
        for item in self.items:
            if item.publication != None:
                for type in item.publication:
                    type_count[type] = type_count.get(type, 0) + 1
        
        return type_count
    
    def publication_years(self):
        '''Return a dictionary counting papers each year.'''
        year_count = {}
        for item in self.items:
            try:
                year = item.date.split("-")[0]
            except:
                continue
            year_count[year] = year_count.get(year,0) + 1
    
        return year_count
    
    def paper_citations(self):
        '''Return a dictionary of papers' citaiton counts.'''
        return dict([(item.arxiv_id, len(item.citations)) for item in self.items])
    