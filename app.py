import re
import os
import uuid
import tiktoken
from flask import Flask, request, jsonify
from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain.embeddings import CohereEmbeddings


# cohere密钥
cohere_api_key = os.getenv('COHERE_API_KEY', "")

app = Flask(__name__)

# tiktoken计算
encoding = tiktoken.get_encoding("cl100k_base")
encoding = tiktoken.encoding_for_model("text-embedding-ada-002")
def num_tokens_from_string(string: str, encoding_name: str) -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

@app.route('/file_embed', methods=['POST'])
def file_embed():
    try:
        # 检查是否上传了文件
        if 'file' not in request.files:
            raise ValueError('未上传文件')

        file = request.files['file']

        # 检查文件扩展名
        if not file.filename.endswith('.pdf') and not file.filename.endswith('.txt'):
            raise ValueError('无效的文件格式')

        # 将文件保存到临时目录
        uuid_filename = str(uuid.uuid4())
        filename_with_uuid = f'{uuid_filename}_{file.filename}'
        temp_file_path = f'uploads/{filename_with_uuid}'
        file.save(temp_file_path)

        splitte_text = []
        data_text = ""  # 存储所有metadata的字符串变量
        tokens = 0 # tokens

        if file.filename.endswith('.pdf'):
            # 创建一个PDF加载器并加载文件
            loader = PyPDFLoader(temp_file_path)
            pages = loader.load_and_split()
            for page in pages:
                data_text += page.page_content + " " 
                tokens += num_tokens_from_string(page.page_content, "cl100k_base")
        if file.filename.endswith('.txt'):
            loader = UnstructuredFileLoader(temp_file_path)
            pages = loader.load()
            for page in pages:
                data_text += page.page_content + " " 
                tokens += num_tokens_from_string(page.page_content, "cl100k_base")

        # 检查内容是否为空
        if not data_text.strip():
            raise ValueError('文件内容为空')
        
        # 删除上传的文件
        os.remove(temp_file_path)

        fromtext = re.sub(r'\s+', '\n', data_text.strip())
        
        # 创建一个文本分割器并分割文本
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size = 500,
            chunk_overlap  = 20,
            length_function = len,
        )
        texts = text_splitter.create_documents([fromtext])

        # 创建一个嵌入器并嵌入文档
        embeddings = CohereEmbeddings(cohere_api_key=cohere_api_key)
        # 将分割后的文本存储到列表中
        for page in texts:
            splitte_text.append({
                'content': page.page_content,
                'embedddoc': embeddings.embed_documents([page.page_content])
            })
        
        # 返回转换后的内容
        return jsonify({
            'preview': splitte_text,
            'tokens': tokens
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run()