import argparse
from racp.retriver import Retriver
from racp.data import RawSet 
from racp.utils import ConfigObject


def main(args):
    ## test retriver 
    config = ConfigObject(vars(args))
    database = RawSet()
    print("Loading dataset...")
    database.load(config.db_path)
    retriver = Retriver(config,database)
    while True:
        query = input("请输入查询文本：")
        result = retriver.retrival(query)
        print(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Perform similarity search on documents.")
    # parser.add_argument("--file_path", type=str, default='./data/2308.10874.json', help="Path to the JSON file.")
    parser.add_argument("--db_path", type=str, help="Path to the dataset.")
    parser.add_argument("--loader_file_path", type=str, default='./test.json', help="Path for JSONLoader.")
    parser.add_argument("--loader_jq_schema", type=str, default='.[].abstract', help="jq schema for JSONLoader.")
    parser.add_argument("--chunk_size", type=int, default=1000, help="Chunk size for text splitting.")
    parser.add_argument("--chunk_overlap", type=int, default=0, help="Chunk overlap for text splitting.")
    parser.add_argument("--model_name", type=str, default="sentence-transformers/all-mpnet-base-v2", help="Hugging Face model name.")
    parser.add_argument("--device", type=str, default="cuda", help="Device for HuggingFaceEmbeddings.")
    parser.add_argument("--normalize_embeddings", action="store_true", help="Normalize embeddings in HuggingFaceEmbeddings.")
    #parser.add_argument("--query", type=str, default="'Research automation efforts usually employ AI as a tool to automate specific\ntasks within the research process. To create an AI that truly conduct research\nthemselves, it must independently generate hypotheses, design verification\nplans, and execute verification. Therefore, we investigated if an AI itself")
    args = parser.parse_args()
    main(args)
