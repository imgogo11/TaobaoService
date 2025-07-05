import os
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
# from langchain.tools.render import render_text_for_llm

# 导入DeepSeek聊天模型
from langchain_deepseek.chat_models import ChatDeepSeek

# 导入用于调用类OpenAI格式API的Embeddings类
from langchain_openai import OpenAIEmbeddings

# 从配置文件中导入API密钥
from config import DEEPSEEK_API_KEY, SILICONFLOW_API_KEY

# 从工具文件中导入可用的函数
from tools import available_tools, query_order_status, query_product_info

# 为DeepSeek设置环境变量API Key（langchain-deepseek库需要）
os.environ["DEEPSEEK_API_KEY"] = DEEPSEEK_API_KEY

class TaobaoChatbot:
    """
    一个集成了RAG（检索增强生成）和工具调用（Function Calling）的淘宝智能客服。
    - 使用 DeepSeek API (deepseek-chat) 作为核心对话模型。
    - 使用 硅基流动(SiliconFlow) API (Qwen/Qwen3-Embedding-0.6B) 进行文本嵌入。
    """

    def _find_latest_vectorstore_path(self) -> str:
        """
        扫描 knowledge_base 目录，找到最新的 FAISS 索引文件夹。
        文件夹命名规则应为 'faiss_index_sf_YYYYMMDD_HHMM'。
        """
        knowledge_base_dir = "knowledge_base"
        
        # 检查知识库目录是否存在
        if not os.path.exists(knowledge_base_dir):
            raise FileNotFoundError(f"知识库目录不存在: '{knowledge_base_dir}'。请先运行 'knowledge_base_builder.py'。")
            
        # 找出所有符合命名规则的文件夹
        all_index_dirs = [d for d in os.listdir(knowledge_base_dir) 
                          if os.path.isdir(os.path.join(knowledge_base_dir, d)) and d.startswith("faiss_index_sf_")]
        
        # 如果找不到任何索引文件夹，则报错
        if not all_index_dirs:
            raise FileNotFoundError(f"在 '{knowledge_base_dir}' 中未找到任何 'faiss_index_sf_*' 格式的知识库。")
            
        # 基于时间戳（文件夹名称）进行排序，找到最新的一个
        # 因为时间格式是 YYYYMMDD_HHMM，所以可以直接按字符串排序
        latest_dir = sorted(all_index_dirs)[-1]
        
        return os.path.join(knowledge_base_dir, latest_dir)

    def __init__(self):
        print("正在初始化基于DeepSeek(聊天)和硅基流动(嵌入)的智能客服...")
        
        # 1. 初始化聊天模型 (LLM)
        # 使用langchain-deepseek库，它会自动处理API密钥
        self.llm = ChatDeepSeek(model="deepseek-chat")
        
        # 2. 绑定工具
        # 将我们定义的Python函数绑定到LLM，使其能够调用这些工具
        self.llm_with_tools = self.llm.bind_tools(available_tools)

        # 3. 初始化并加载知识库
        # 3.1. 初始化嵌入模型 (Embeddings)
        # 使用OpenAIEmbeddings类来调用硅基流动的API，因为其格式兼容
        embeddings = OpenAIEmbeddings(
            model="Qwen/Qwen3-Embedding-0.6B",      # 在硅基流动上选择的嵌入模型
            base_url="https://api.siliconflow.cn/v1", # 硅基流动的API端点
            api_key=SILICONFLOW_API_KEY              # 传入硅基流动的API密钥
        )
        
        # 3.2. 加载本地FAISS向量数据库
        # 确保这个路径与knowledge_base_builder.py中保存的路径一致
        # vectorstore_path = "knowledge_base/faiss_index_sf"
        # print(f"正在从 '{vectorstore_path}' 加载知识库...")
        # self.vectorstore = FAISS.load_local(vectorstore_path, embeddings, allow_dangerous_deserialization=True)
        try:
            vectorstore_path = self._find_latest_vectorstore_path()
            print(f"检测到最新知识库，正在从 '{vectorstore_path}' 加载...")
            self.vectorstore = FAISS.load_local(vectorstore_path, embeddings, allow_dangerous_deserialization=True)
        except FileNotFoundError as e:
            print(f"错误: {e}")
            # 如果找不到知识库，可以选择退出程序或进行其他处理
            exit()
        
        # 3.3. 创建检索器 (Retriever)
        # 检索器负责根据用户问题从向量数据库中找出最相关的文本片段
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3}) # "k": 3 表示返回最相关的3个片段

        # 4. 初始化对话历史
        # SystemMessage定义了AI的角色和行为准则
        self.chat_history = [
            SystemMessage(content="你是'潮流前线'店铺的AI智能客服'小潮'。你的任务是友好、专业地回答顾客问题。你可以调用工具查询商品信息、订单状态，并利用知识库解答常见问题。如果知识库信息和工具查询结果冲突，优先相信工具的实时结果。回答时要像一个真实的、热情的淘宝客服。")
        ]
        
        print("智能客服'小潮' (DeepSeek + SiliconFlow) 已启动，可以开始提问了！")
    
    def _get_retrieved_context(self, query: str) -> str:
        """
        一个私有方法，用于从向量数据库中检索与查询相关的上下文信息。
        """
        retrieved_docs = self.retriever.invoke(query)
        context = "\n\n".join([doc.page_content for doc in retrieved_docs])
        return context

    def chat(self, query: str) -> str:
        """
        处理单次用户查询的核心函数。
        """
        # 步骤 1: 从知识库检索相关上下文 (RAG的第一步)
        retrieved_context = self._get_retrieved_context(query)
        
        # 步骤 2: 构建包含上下文、历史和当前问题的Prompt
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """
            你是一个淘宝店铺的智能客服。根据下面提供的“知识库上下文”和“工具”来回答问题。
            如果问题明显需要实时信息（如订单状态、库存），优先使用工具。
            如果问题是关于商品介绍、店铺政策等，优先使用知识库。
            如果两者都相关，结合信息进行回答。
            保持友好和热情的语气。

            --- 知识库上下文 ---
            {context}
            --------------------
            """),
            ("placeholder", "{chat_history}"), # 用于插入历史对话
            ("human", "{input}")              # 用于插入当前用户问题
        ])
        
        # 将Prompt和绑定了工具的LLM链接起来，形成一个处理链(Chain)
        chain = prompt_template | self.llm_with_tools
        
        # 步骤 3: 第一次调用LLM，让它决策是直接回答还是调用工具
        response = chain.invoke({
            "context": retrieved_context,
            "chat_history": self.chat_history,
            "input": query
        })

        # 步骤 4: 处理LLM的响应
        # 情况A: LLM决定调用一个或多个工具
        if response.tool_calls:
            tool_results = []
            # 遍历所有工具调用请求
            for tool_call in response.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                
                print(f"---LLM决定调用工具: {tool_name}，参数: {tool_args}---")
                
                # 在这里我们手动执行工具，实际应用中可以有更优雅的路由
                if tool_name == "query_order_status":
                    result = query_order_status(**tool_args)
                elif tool_name == "query_product_info":
                    result = query_product_info(**tool_args)
                else:
                    result = f"未知的工具: {tool_name}"
                
                # 将工具的执行结果打包成ToolMessage
                tool_results.append(ToolMessage(content=str(result), tool_call_id=tool_call['id']))
            
            # 将用户问题、LLM的工具调用决策、以及工具的执行结果都加入到历史中
            self.chat_history.append(HumanMessage(content=query))
            self.chat_history.append(response) # AIMessage with tool_calls
            self.chat_history.extend(tool_results)
            
            # 第二次调用LLM，让它基于工具的返回结果，生成最终给用户的回复
            final_response = self.llm.invoke(self.chat_history)
            ai_response_content = final_response.content
        else:
            # 情况B: LLM决定不调用工具，直接回答
            # 将用户问题和LLM的直接回答加入历史
            self.chat_history.append(HumanMessage(content=query))
            self.chat_history.append(response)
            ai_response_content = response.content

        return ai_response_content