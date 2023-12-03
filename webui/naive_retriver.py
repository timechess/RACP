import json
from pathlib import Path
import argparse
from pprint import pprint
from langchain.document_loaders import JSONLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings

import racp 
from racp.data import RawSet 
from racp.utils import load_config 
def load_json(file_path):
    return json.loads(Path(file_path).read_text())
class Retriver():
    def __init__(self,config=None,dataset=None) -> None:
        self.text_splitter = CharacterTextSplitter(chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap)
        self.build_embedding_model(config)
        if dataset is None:
            self.build_retriver_from_json(config)
        else:
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
        data = [i.to_Document() for k,i in enumerate(dataset) if k < 100]
        print(f'Loaded {len(data)} documents using dataset ')
        documents = self.text_splitter.split_documents(data)
        self.db = Chroma.from_documents(documents,self.hf)
    def retrival(self,query,k=10):
        docs = self.db.similarity_search_with_relevance_scores(query,k=k)
        result = [{'Papername':doc[0].metadata['title'],'arxiv_id':doc[0].metadata['source'],'relevance':doc[1]} for doc in docs if doc[1]>0]
        return result 
        # return  f"Most similar document's page content:\n{docs[0].page_content}"
def main(args):
    ## test retriver 
    config = load_config("./retriver_config.yaml")
    database = RawSet(config.dbpath)
    print(len(database))
    retriver = Retriver(config,database)
    docs = retriver.retrival("'Research automation efforts usually employ AI as a tool to automate specific\ntasks within the research process. To create an AI that truly conduct research\nthemselves, it must independently generate hypotheses, design verification\nplans, and execute verification. Therefore, we investigated if an AI itself")
    print(len(docs))
    print(docs[0])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Perform similarity search on documents.")
    parser.add_argument("--file_path", type=str, default='./data/2308.10874.json', help="Path to the JSON file.")
    parser.add_argument("--loader_file_path", type=str, default='./test.json', help="Path for JSONLoader.")
    parser.add_argument("--loader_jq_schema", type=str, default='.[].abstract', help="jq schema for JSONLoader.")
    parser.add_argument("--chunk_size", type=int, default=1000, help="Chunk size for text splitting.")
    parser.add_argument("--chunk_overlap", type=int, default=0, help="Chunk overlap for text splitting.")
    parser.add_argument("--model_name", type=str, default="sentence-transformers/all-mpnet-base-v2", help="Hugging Face model name.")
    parser.add_argument("--device", type=str, default="cpu", help="Device for HuggingFaceEmbeddings.")
    parser.add_argument("--normalize_embeddings", action="store_true", help="Normalize embeddings in HuggingFaceEmbeddings.")
    parser.add_argument("--query", type=str, default="What did the president say about Ketanji Brown Jackson", help="Query for similarity search.")
    args = parser.parse_args()

    main(args)
