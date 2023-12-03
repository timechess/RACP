from flask import Flask, render_template, request, session
import secrets
server_key="GKlG2S2Uz3IK"
# 生成一个包含 32 字节随机十六进制字符串的密钥
secret_key = secrets.token_hex(32)
app = Flask(__name__)
app.secret_key = secret_key  # 设置用于加密 session 数据的密钥
class ConfigObject:
    def __init__(self, config_dict):
        self.__dict__.update(config_dict)

def load_config(config_path):
    with open(config_path, 'r') as config_file:
        config_data = yaml.safe_load(config_file)

    if config_data is not None:
        return ConfigObject(config_data)
    else:
        return None


import argparse
import yaml
from naive_retriver import Retriver
config = load_config("./retriver_config.yaml")
retriver = Retriver(config)

def process_text_and_file(input_text, uploaded_file):
    if input_text:
        return f"Processed Text: {input_text}"
    elif uploaded_file:
        file_content = uploaded_file.read().decode('utf-8')
        return f"File Content: {file_content}"
    else:
        return ""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 获取文本输入
        input_text = request.form['input_text']

        # 获取上传的文件
        uploaded_file = request.files['file_input']

        # 处理文本输入和文件
        processed_text = process_text_and_file(input_text, uploaded_file)

        # 将结果存储在 session 中，以便在下一次请求时使用
        session['processed_text'] = processed_text
        result = retriver.retrival(processed_text)
        session['retrieval_results'] = result
        return render_template('index.html', input_text=input_text, processed_text=result)

    # 如果是 GET 请求，清空之前的结果
    session.pop('processed_text', None)
    session.pop('retrieval_results', None)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(port=6006,debug=True)