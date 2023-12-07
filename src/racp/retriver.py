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
    def __init__(self,config=None,dataset=None) -> None:
        self.text_splitter = CharacterTextSplitter(chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap)
        self.build_embedding_model(config)
        if dataset is None:
            print("JSON")
            self.build_retriver_from_json(config)
        else:
            print("Dataset")
            self.build_retriver_from_dataset(dataset)
    def build_embedding_model(self,config):
        # Initialize HuggingFaceEmbeddings
        model_kwargs = {'device': config.device}
        encode_kwargs = {'normalize_embeddings': config.normalize_embeddings}
        self.hf = HuggingFaceEmbeddings(model_name=config.model_name, model_kwargs=model_kwargs, encode_kwargs=encode_kwargs)
    def build_retriver_from_json(self,config):
        # Initialize JSONLoader
        loader = JSONLoader(file_path=config.loader_file_path, jq_schema=config.loader_jq_schema, text_content=False)
        data = loader.load()
        print(f'Loaded {len(data)} documents using JSONLoader')
        # Split documents using CharacterTextSplitter
        documents = self.text_splitter.split_documents(data)
        # Load documents into Chroma vector store
        self.db = Chroma.from_documents(documents, self.hf)
    def build_retriver_from_dataset(self,dataset):
        # TODO : remove k < 2000 
        data = [i.to_Document() for k,i in enumerate(dataset) if k < 2000 ]
        print(f'Loaded {len(data)} documents using dataset ')
        documents = self.text_splitter.split_documents(data)
        self.db = Chroma.from_documents(documents,self.hf)
    def retrival(self,query,k=10):
        docs = self.db.similarity_search_with_relevance_scores(query,k=k)
        result = [{'Papername':doc[0].metadata['title'],'arxiv_id':doc[0].metadata['source'],'quality':doc[0].metadata['quality'],'relevance':doc[1],} for doc in docs if doc[1]>0]
        return result 
        # return  f"Most similar document's page content:\n{docs[0].page_content}"
    # TODO: other retrival policy 
