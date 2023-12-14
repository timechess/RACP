import json
from pathlib import Path
import argparse
from pprint import pprint
from langchain.document_loaders import JSONLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings

def load_json(file_path):
    return json.loads(Path(file_path).read_text())
class Retriver():
    """retriever 
    
    """
    def __init__(self, config=None, database=None) -> None:
        """Initialize retriever using config and database
        
        Args:
            config (Config): configuration for the retriever.
            database (list): a list of Document objects to build the retriever from.
        """
        self.text_splitter = CharacterTextSplitter(chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap)
        self.build_embedding_model(config)
        if database is not None:
            self.build_retriver_from_database(database)
        else:
            raise ValueError('Please specify database')
        
    def build_embedding_model(self, config):
        """Initialize HuggingFaceEmbeddings
        
        Args:
            config (Config): configuration for the retriever.
        """
        model_kwargs = {'device': config.device}
        encode_kwargs = {'normalize_embeddings': config.normalize_embeddings}
        self.hf = HuggingFaceEmbeddings(model_name=config.model_name, model_kwargs=model_kwargs, encode_kwargs=encode_kwargs)
    def build_retriver_from_database(self, database):
        """Build the retriever from the database
        
        Args:
            database (list): a list of Document objects to build the retriever from.
        """
        # TODO : remove k < 2000 
        # data = [i.to_Document() for k,i in enumerate(database) if k < 2000 ]
        data = [i.to_Document() for k,i in enumerate(database) ]
        print(f'Loaded {len(data)} documents using database ')
        documents = self.text_splitter.split_documents(data)
        ## check duplicate 
        ids = set([doc.metadata['source'] for doc in documents])
        print(len(ids),len(documents))
        self.db = Chroma.from_documents(documents,self.hf)
    def retrival(self, query, k=10):
        """Perform retrieval
        
        Args:
            query (str): the query to search for in the retriever.
            k (int): number of documents to return.
            
        Returns:
            list: a list of dictionaries containing information about the retrieved documents.
        """
        docs = self.db.similarity_search_with_relevance_scores(query,k=k*2)
        result = [{'Papername':doc[0].metadata['title'],'arxiv_id':doc[0].metadata['source'],'quality':doc[0].metadata['quality'],'relevance':doc[1]} for doc in docs if doc[1]>0]
        arxivids = list(set([doc[0].metadata['source'] for doc in docs if doc[1] > 0]))

        unique_result = []
        for doc in docs:
            if doc[1] > 0:
                arxiv_id = doc[0].metadata['source']
                if arxiv_id  in arxivids:
                    unique_result.append({'Papername': doc[0].metadata['title'], 'arxiv_id': doc[0].metadata['source'], 'quality': doc[0].metadata['quality'], 'relevance': doc[1]})
                    arxivids.remove(arxiv_id)
        print(unique_result)
        return unique_result 
        # return  f"Most similar document's page content:\n{docs[0].page_content}"
    # TODO: other retrival policy 
