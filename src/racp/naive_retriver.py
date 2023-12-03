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

def main(args):
    # Load JSON data from the specified file
    data = load_json(args.file_path)

    # Initialize JSONLoader
    loader = JSONLoader(file_path=args.loader_file_path, jq_schema=args.loader_jq_schema, text_content=False)
    data = loader.load()
    print(f'Loaded {len(data)} documents using JSONLoader')

    # Split documents using CharacterTextSplitter
    text_splitter = CharacterTextSplitter(chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap)
    documents = text_splitter.split_documents(data)

    # Initialize HuggingFaceEmbeddings
    model_kwargs = {'device': args.device}
    encode_kwargs = {'normalize_embeddings': args.normalize_embeddings}
    hf = HuggingFaceEmbeddings(model_name=args.model_name, model_kwargs=model_kwargs, encode_kwargs=encode_kwargs)

    # Load documents into Chroma vector store
    db = Chroma.from_documents(documents, hf)
    
    # Perform similarity search using the query
    query = args.query
    docs = db.similarity_search(query)
    print(f"Most similar document's page content:\n{docs[0].page_content}")

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
