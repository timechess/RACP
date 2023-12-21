import os
import json
import jsonlines
from tqdm import tqdm
import racp.crawl as crawl
from racp.utils import save_json,ccbc 
from torch.utils.data import Dataset
import numpy as np 
from datetime import datetime
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
        self._quality = None 
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
        """Convert to document format"""
        from langchain_core.documents.base import Document
        abstract = self.abstract
        content = self.content
        if abstract is None:
            abstract = self.content[:250]
        # TODO : content retrival 
        if abstract is None:
            abstract = ""
        metadata = {"source":self.arxiv_id,"title":self.title,"quality":self.quality}
        metadata = {"source":self.arxiv_id,"title":self.title,"quality":str(self.quality)}
        doc = Document(metadata=metadata,page_content=abstract)
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
    @property
    def quality(self):
        """Evaluate confidence quality."""
        if self._quality is None:  # Calculate only if not computed yet
            # TODO: normalize citation 
            cite_num = len(self.citations)
            # pubdate = datetime.strptime(self.date, "%Y-%m-%d").date()
            # today = datetime.now().date()
            # days_diff = (today - pubdate).days
            # cite_diff =  cite_num/ days_diff
            cite_score =  np.log(cite_num+1) # the citation larger than dozens is enough for reality 
            # TODO: Author score considering the history of publication
            author_score = 0 
            # x = (days_diff / 225)
            # dates_core = np.e * x * np.exp(-x)
            dates_core=0
            self._quality = dates_core+cite_score+ author_score 

        return self._quality
            
            
        
        

class RawSet(Dataset):
    '''A torch Dataset storing raw data.'''
    def __init__(self, save_path=None,length = -1 ) -> None:
        super().__init__()
        self.items = []  # List of PaperItems
        self.id2idx = {}
        if save_path != None:
            self._load_from_directory(save_path,length)

    def _load_from_directory(self, save_path,length = -1 ):
        '''Load json files from given directory.'''
        filenames = os.listdir(save_path)
        for idx, file in tqdm(enumerate(filenames), total=len(filenames)):
            path = os.path.join(save_path, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except:
                print(path)
                continue
            item = PaperItem()
            item.load_json(data)
            self.id2idx[item.arxiv_id] = idx
            self.items.append(item)
            # TODO : remove for deveplop 
            if length>0 and len(self.items)>length:
                break
    
    def add_item(self, item : PaperItem):
        self.items.append(item)
    
    def get_item_by_arxivid(self,arxiv_id):
        if self.id2idx.get(arxiv_id,-1) !=-1:
            return self.items[self.id2idx[arxiv_id]]
        else:
            return -1 
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
    def topk(self, paper, k=100):
        """Return top k relevance paper"""
        sim = np.zeros(self.__len__())
        for i in range(self.__len__()):
            paper_i = self.__getitem__(i)
            sim[i] = ccbc(paper, paper_i)
        
        # 使用np.argsort获取排序后的索引数组
        print(sim)
        print(np.argsort(sim))
        print(k,type(k))
        topk_indices = np.argsort(sim)[::-1][:k]
        # 获取对应的top k项
        topk_items = [self.__getitem__(i) for i in topk_indices]
        return topk_items
    def load_from_papers(self,papers):
        """Build dataset from papers list """
        for paperitem in papers:
            self.items.append(paperitem)