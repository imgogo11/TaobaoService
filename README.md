# 淘宝智能客服 (Taobao AI Customer Service)

这是一个基于大型语言模型（LLM）构建的、功能完备的电商智能客服项目。它不仅仅是一个简单的问答机器人，而是一个集成了**检索增强生成 (RAG)** 和 **工具调用 (Tool Calling)** 的高级AI代理。

## 核心功能

*   **多源知识库问答 (RAG):** 能够理解用户用自然语言提出的开放性问题（如“商品如何保养？”），并从本地知识库中检索最相关的信息，生成流畅的回答。
*   **实时数据查询 (Tool Calling):** 能够调用外部工具，查询结构化数据，以完成需要精确信息的任务（如“查询订单D001的状态”、“查询某T恤的L码库存”）。
*   **Web交互界面:** 提供一个基于`Streamlit`的友好、直观的聊天界面。
*   **命令行模式:** 支持在终端中运行，方便快速测试和调试。

## 技术栈

*   **核心框架:** LangChain
*   **语言模型 (LLM):** DeepSeek (通过 `langchain-deepseek` 调用)
*   **嵌入模型 (Embedding):** Qwen/Qwen3-Embedding-0.6B (通过 `SiliconFlow` 硅基流动 API 调用)
*   **向量数据库:** FAISS (Facebook AI Similarity Search)
*   **Web框架:** Streamlit
*   **数据处理:** Pandas

## 项目结构简介

```
.
├── app.py                  # Streamlit Web应用入口
├── chatbot.py              # 核心控制器，封装了RAG和工具调用逻辑
├── tools.py                # 定义了可供AI调用的工具（查订单、查商品）
├── knowledge_base_builder.py # 用于构建和更新FAISS向量知识库的脚本
├── transform_ecd.py        # 用于清洗和转换原始数据集的预处理脚本
├── config.py.example       # API密钥配置文件的示例
├── requirements.txt        # 项目依赖
├── data/                     # 存放处理好的、可直接使用的数据源
│   ├── products.csv
│   └── ...
├── E-commerce dataset/     # 存放原始数据集（需自行下载）
│   └── ...
└── knowledge_base/         # 存放生成的FAISS索引文件（此目录由脚本自动创建）
```

## 安装与配置

请严格按照以下步骤进行，以确保项目能够成功运行。

### 1. 克隆项目
```bash
git clone https://github.com/imgogo11/TaobaoService.git
cd TaobaoService
```

### 2. 安装依赖
项目所需的所有Python库都记录在`requirements.txt`中。
```bash
pip install -r requirements.txt
```

### 3. 配置API密钥
本项目需要调用DeepSeek和硅基流动的API。

1.  将 `config.py.example` 文件复制一份并重命名为 `config.py`。
2.  在 `config.py` 文件中填入你自己的API密钥。

```python
# config.py
DEEPSEEK_API_KEY = "你的deepseek_api_key"
SILICONFLOW_API_KEY = "你的siliconflow_api_key"
```

### 4. 准备数据源
本项目的数据分为两部分：

*   **自有数据:** `data`目录下的`faq.txt`, `orders.csv`, `products.csv`已提供。
*   **外部数据集:** 项目使用`E-commerce dataset`来丰富FAQ知识。
    1.  请从以下地址下载数据集并解压：[Google Drive链接](https://drive.google.com/file/d/154J-neBo20ABtSmJDvm7DK0eTuieAuvw/view)
    2.  将解压后的`train.txt`等文件放到项目根目录下的`E-commerce dataset`文件夹内。
    3.  运行数据预处理脚本，将原始数据转换为问答对格式：
        ```bash
        python transform_ecd.py
        ```

### 5. 构建知识库 (关键步骤！)
在首次运行或更新知识（如修改了`faq.txt`）后，**必须**运行此脚本来创建或更新向量数据库。
```bash
python knowledge_base_builder.py
```
成功运行后，你会在`knowledge_base`目录下看到一个带时间戳的索引文件夹。

## 运行方式

我们提供两种运行方式：

### 1. Web界面 (推荐)
启动一个美观、易用的聊天网页应用。
```bash
streamlit run app.py
```

### 2. 命令行模式 (用于测试和调试)
在终端中直接与机器人进行对话。
```bash
python main.py
```

## 备注
请先在 `config.py` 中配置好你的 API Key
知识库构建时间可能较长，请耐心等待
项目目前模拟数据库为CSV，生产环境可替换为真实数据库接入