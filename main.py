import os
from chatbot import TaobaoChatbot

def check_for_knowledge_base():
    """
    检查 'knowledge_base' 目录下是否存在任何一个 FAISS 索引文件夹。
    返回 True 如果存在，否则返回 False。
    """
    knowledge_base_dir = "knowledge_base"
    
    # 首先检查根目录是否存在
    if not os.path.exists(knowledge_base_dir):
        return False
        
    # 遍历目录下的所有条目
    for item in os.listdir(knowledge_base_dir):
        # 检查是否是文件夹并且名字符合我们的规则
        if os.path.isdir(os.path.join(knowledge_base_dir, item)) and item.startswith("faiss_index_sf_"):
            return True # 只要找到一个，就说明知识库存在
            
    return False # 如果遍历完都没找到，说明不存在

def main():
    # --- 核心修改：使用新的检查函数 ---
    if not check_for_knowledge_base():
        print("错误：在 'knowledge_base' 目录下未检测到任何知识库。")
        print("请先运行 'python knowledge_base_builder.py' 来构建一个。")
        return
    # ---------------------------------

    # 实例化 TaobaoChatbot
    # TaobaoChatbot 内部会自动加载最新的知识库
    try:
        bot = TaobaoChatbot()
    except Exception as e:
        print(f"初始化聊天机器人时发生严重错误: {e}")
        return

    print("-" * 50)
    print("欢迎来到'潮流前线'！我是您的智能客服'小潮'。")
    print("您可以问我关于商品、订单的问题，或者输入 'exit' 退出。")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("您: ")
            if user_input.lower() == 'exit':
                print("小潮: 感谢您的光临，期待下次再见！")
                break
            
            ai_response = bot.chat(user_input)
            print(f"小潮: {ai_response}")

        except Exception as e:
            print(f"在对话过程中发生错误: {e}")
            break

if __name__ == "__main__":
    main()