import streamlit as st
import os
from chatbot import TaobaoChatbot

# --- 辅助函数，用于检查知识库是否存在 ---
def check_for_knowledge_base():
    """
    检查 'knowledge_base' 目录下是否存在任何一个 FAISS 索引文件夹。
    返回 True 如果存在，否则返回 False。
    """
    knowledge_base_dir = "knowledge_base"
    
    if not os.path.exists(knowledge_base_dir):
        return False
        
    for item in os.listdir(knowledge_base_dir):
        if os.path.isdir(os.path.join(knowledge_base_dir, item)) and item.startswith("faiss_index_sf_"):
            return True
            
    return False

# --- 页面配置 ---
st.set_page_config(
    page_title="潮流前线 - 智能客服",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="auto"
)

st.title("潮流前线 - 智能客服 '小潮' 🤖")
st.caption("我是您的专属购物助手，可以回答商品、订单和店铺问题。")

# --- 初始化聊天机器人 ---
# 使用 session_state 来持久化机器人实例，避免每次交互都重新加载
if 'bot' not in st.session_state:
    # --- 核心修改：使用新的检查函数 ---
    if not check_for_knowledge_base():
        # 如果找不到知识库，显示错误信息并停止应用执行
        st.error("错误：在 'knowledge_base' 目录下未检测到任何知识库。")
        st.info("请先在终端中运行 'python knowledge_base_builder.py' 来构建一个。")
        st.stop()
    # ---------------------------------
    
    # 加上 try-except 以处理可能的初始化失败
    try:
        # 显示一个加载状态，提升用户体验
        with st.spinner("正在启动智能客服'小潮'，请稍候... (首次启动加载会稍慢)"):
            # 实例化 TaobaoChatbot，它会自动加载最新的知识库
            st.session_state.bot = TaobaoChatbot()
    except Exception as e:
        st.error(f"机器人初始化失败，错误信息: {e}")
        st.stop()


# --- 初始化聊天历史 ---
# st.session_state 就像一个可以跨交互轮次共享的字典
if "messages" not in st.session_state:
    # 手动创建一个欢迎语作为第一条消息
    st.session_state.messages = [{"role": "assistant", "content": "亲，您好！我是'潮流前线'的智能客服'小潮'，有什么可以帮您的吗？"}]

# --- 显示聊天历史 ---
# 遍历 session_state 中的所有消息并显示出来
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 处理用户输入 ---
# st.chat_input 会在页面底部创建一个输入框
if prompt := st.chat_input("请输入您的问题..."):
    # 1. 在界面上显示用户自己的问题
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. 调用机器人获取AI的回答
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        # 显示一个"思考中"的提示
        with st.spinner("小潮正在思考中..."):
            try:
                # 调用 chatbot 的核心方法
                ai_response = st.session_state.bot.chat(prompt)
                message_placeholder.markdown(ai_response)
            except Exception as e:
                error_message = f"抱歉，处理您的问题时遇到了麻烦: {e}"
                message_placeholder.markdown(error_message)
                ai_response = error_message
    
    # 3. 将AI的回答也加入到历史记录中，以便下次刷新时能显示
    st.session_state.messages.append({"role": "assistant", "content": ai_response})