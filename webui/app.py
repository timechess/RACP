from flask import Flask, render_template, request, session
import secrets
server_key="GKlG2S2Uz3IK"
# 生成一个包含 32 字节随机十六进制字符串的密钥
secret_key = secrets.token_hex(32)
app = Flask(__name__)
app.secret_key = secret_key  # 设置用于加密 session 数据的密钥

import argparse
import yaml
from racp.naive_retriver import Retriver
from racp.data import PaperItem ,RawSet
from racp import utils 
print("start loading database...")
config = utils.load_config("./retriver_config.yaml")
database = RawSet(config.dbpath,length = 100)
print("start loading retriver...")
retriver = Retriver(config,database)
print("initialization end ... ")

def process_text_and_file(input_text, uploaded_file):
    """return string of raw text """
    if input_text:
        return f"Processed Text: {input_text}"
    elif uploaded_file:
        # TODO:  解析pdf 文件 抓取里面的文本 
        file_content = uploaded_file.read().decode('utf-8')
        return f"File Content: {file_content}"
    else:
        return ""

def process_arxiv_id(arxiv_id,k=1000):
    # 根据arxiv id 爬 pdf -> 文档 
    try:
        paper = PaperItem(arxiv_id=arxiv_id)
        topkitems = database.topk(paper,k=k)
        topkpaper = RawSet()
        topkpaper.load_from_papers(topkitems)
        # build retriver 
        local_retriver = Retriver(config,topkpaper)
        result = local_retriver.retrival(paper.abstract,k=10)
    except ConnectionError as e:
        result = e 
        print(e)
    
    return {"topk":result,"abstract":paper.abstract}
        
        
    
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 获取文本输入和文件上传
        print("get input ")
        input_text = request.form['input_text']
        uploaded_file = request.files['file_input']

        # 获取arXiv ID输入
        arxiv_id = request.form['arxiv_id']

        # 处理arXiv ID
        if arxiv_id:
            print(arxiv_id)
            # 调用处理arXiv ID的函数
            arxiv_result = process_arxiv_id(arxiv_id)
            session['processed_text'] = arxiv_result['abstract']
            session['arxiv_result'] = arxiv_result['topk']
            # 将arXiv结果存储在session中
        else:
        # 处理文本输入和文件
            processed_text = process_text_and_file(input_text, uploaded_file)
            # 将结果存储在session中，以便在下一次请求时使用
            session['processed_text'] = processed_text
            result = retriver.retrival(processed_text)
            session['arxiv_result'] = result
        
        print(session['processed_text'])
        # convert arxiv id to arxiv link 
        # 将结果存储在 session 中，以便在下一次请求时使用
        return render_template('index.html', input_text=input_text, processed_text=session['processed_text'], table_data=session['arxiv_result'])

    # 如果是GET请求，清空之前的结果
    session.pop('processed_text', None)
    session.pop('retrieval_results', None)
    session.pop('arxiv_result', None)
    return render_template('index.html')
if __name__ == '__main__':
    app.run(port=6006,debug=True)