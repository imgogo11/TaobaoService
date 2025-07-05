import os
import datetime
import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader, CSVLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from config import SILICONFLOW_API_KEY

def load_product_docs(csv_path):
    df = pd.read_csv(csv_path)
    docs = []
    for _, row in df.iterrows():
        content = f"{row['product_name']}。{row.get('description', '')}"
        docs.append(Document(page_content=content.strip()))
    return docs

def build_knowledge_base():
    """
    加载数据源，切分文本，使用硅基流动API创建向量嵌入并存入FAISS向量库。
    """
    print("开始使用硅基流动(SiliconFlow)API构建知识库...")
    
    # 1. 加载文档 (不变)
    faq_loader = TextLoader('data/faq.txt', encoding='utf-8')
    # product_loader = CSVLoader('data/products.csv', source_column='product_name', encoding='utf-8')
    product_loader = load_product_docs('data/products.csv')
    faq_loader_ecd = TextLoader('data/faq_from_ecd_train.txt', encoding='utf-8')
    # all_docs = faq_loader.load() + product_loader.load() + faq_loader_ecd.load()
    all_docs = faq_loader.load() + product_loader + faq_loader_ecd.load()
    print(f"已加载 {len(all_docs)} 份文档。")

    # 2. 切分文档 (不变)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
    split_docs = text_splitter.split_documents(all_docs)
    print(f"文档已切分为 {len(split_docs)} 个片段。")

    # 3. 初始化硅基流动嵌入模型 (***这里是核心改动***)
    print("正在初始化硅基流动嵌入模型...")
    embeddings = OpenAIEmbeddings(
        model="Qwen/Qwen3-Embedding-0.6B", # <-- 我们选择的模型
        base_url="https://api.siliconflow.cn/v1", # <-- 硅基流动的API地址
        api_key=SILICONFLOW_API_KEY # <-- 你的硅基流动API Key
    )
    print("硅基流动嵌入模型已初始化。")

    # 4. 创建并保存FAISS向量库
    # 建议使用新的索引目录名
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    vectorstore_path = f"knowledge_base/faiss_index_sf_{ts}"
    # vectorstore_path = "knowledge_base/faiss_index_sf"
    vectorstore = FAISS.from_documents(split_docs, embeddings)
    vectorstore.save_local(vectorstore_path)
    
    print(f"知识库构建完成并已保存至 '{vectorstore_path}'。")
    print(f"向量库维度：{vectorstore.index.d}，总向量数：{vectorstore.index.ntotal}")

if __name__ == "__main__":
    if not os.path.exists("knowledge_base"):
        os.makedirs("knowledge_base")
    build_knowledge_base()

