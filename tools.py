# tools.py (基于您提供的CSV数据的最终版本)

import pandas as pd
import os
from typing import Optional

# --- 本地数据源路径配置 ---
PRODUCT_CSV_PATH = 'data/products.csv'
ORDER_CSV_PATH = 'data/orders.csv'

# --- 数据加载辅助函数 ---

def get_product_dataframe() -> pd.DataFrame:
    """动态加载最新的商品CSV文件内容。"""
    if not os.path.exists(PRODUCT_CSV_PATH):
        print(f"错误：商品数据文件未找到于 '{PRODUCT_CSV_PATH}'")
        return pd.DataFrame()
    return pd.read_csv(PRODUCT_CSV_PATH)

def get_order_dataframe() -> pd.DataFrame:
    """动态加载最新的订单CSV文件内容。"""
    if not os.path.exists(ORDER_CSV_PATH):
        print(f"错误：订单数据文件未找到于 '{ORDER_CSV_PATH}'")
        return pd.DataFrame()
    return pd.read_csv(ORDER_CSV_PATH)

# --- LangChain工具函数定义 ---

def query_order_status(order_id: str) -> str:
    """
    根据订单ID从orders.csv文件中查询订单的完整信息，包括状态、物流和收货地址。
    """
    print(f"---TOOL: 正在从CSV查询订单 {order_id} 的状态...---")
    
    df_orders = get_order_dataframe()
    if df_orders.empty:
        return "抱歉，暂时无法访问订单系统，请稍后再试。"
        
    # 根据订单ID筛选订单 (不区分大小写)
    order_details = df_orders[df_orders['order_id'].str.lower() == order_id.lower()]
    
    if order_details.empty:
        return f"抱歉，没有找到订单号为 {order_id} 的信息，请检查订单号是否正确。"
    
    # 从第一行获取订单的通用信息
    first_row = order_details.iloc[0]
    status = first_row['order_status']
    logistics_provider = first_row['logistics_provider']
    logistics_id = first_row['logistics_id']
    shipping_address = first_row['shipping_address']
    
    # 汇总订单内的所有商品名称和数量
    product_list = []
    for _, row in order_details.iterrows():
        product_list.append(f"{row['product_name']} (数量: {row['quantity']})")
    product_summary = ", ".join(product_list)
    
    # 构建结构化的回复
    response = f"订单 {order_id} (包含商品: {product_summary}) 的查询结果如下：\n"
    response += f" - **状态**: {status}\n"
    
    if pd.notna(shipping_address):
        response += f" - **收货地址**: {shipping_address}\n"

    if status == "已发货":
        if pd.notna(logistics_provider) and pd.notna(logistics_id):
            response += f" - **物流信息**: 由 {logistics_provider} 承运，物流单号是 {logistics_id}。"
        else:
            response += " - **物流信息**: 暂未更新，请稍后刷新。"
    elif status == "待发货":
        response += " - **备注**: 我们正在加急为您打包，请您耐心等待。"
    elif status == "已签收":
        response += " - **备注**: 感谢您的惠顾，期待您的再次光临！"
    elif status == "已取消":
        response += " - **备注**: 此订单已被取消。如果您有任何疑问，可以随时联系我们。"
        
    return response

def query_product_info(product_name: str) -> str:
    """
    根据商品名称从products.csv文件中查询其详细信息，包括价格、描述和所有尺码的库存情况。
    """
    print(f"---TOOL: 正在从CSV查询商品 '{product_name}' 的详细信息...---")
    
    df_products = get_product_dataframe()
    if df_products.empty:
        return "抱歉，暂时无法连接到商品数据库，请稍后再试。"
    
    # 进行模糊匹配，找出所有包含关键词的商品
    product_rows = df_products[df_products['product_name'].str.contains(product_name, case=False, na=False)]
    
    if product_rows.empty:
        return f"抱歉，我们店里好像没有找到与'{product_name}'相关的商品哦，您可以换个关键词试试吗？"
    
    if len(product_rows) > 1:
        matched_names = ", ".join(product_rows['product_name'].tolist())
        return f"我们找到了几款相似的商品：{matched_names}。您具体想问哪一款呢？"
        
    # 精确匹配到一个商品
    product = product_rows.iloc[0]
    
    # 获取所有信息并格式化
    name = product['product_name']
    price = product['price']
    description = product['description'] if pd.notna(product['description']) else "暂无详细描述。"
    
    # 动态获取所有 'stock_' 列
    stock_columns = [col for col in df_products.columns if col.startswith('stock_')]
    available_sizes = []
    
    # 遍历所有库存列，构建库存信息
    for col in stock_columns:
        # 确保列存在且值不为空
        if col in product and pd.notna(product[col]):
            stock_count = int(product[col])
            if stock_count > 0:
                # 从列名中提取尺码，例如 'stock_s' -> 'S'
                size_name = col.split('_')[1].upper()
                available_sizes.append(f"{size_name}码({stock_count}件)")
    
    if available_sizes:
        stock_info = f"目前有货的尺码和库存是：{', '.join(available_sizes)}。"
    else:
        # 兼容没有尺码库存或者所有尺码都卖完的情况
        stock_info = "抱歉，这款商品的所有尺码都卖完了。"

    # 构建最终的结构化回复
    response = (
        f"为您找到了商品 '{name}' 的详细信息：\n"
        f" - **价格**: {price} 元\n"
        f" - **商品描述**: {description}\n"
        f" - **库存情况**: {stock_info}"
    )
    return response

# --- 可供LangChain使用的工具列表 ---
available_tools = [query_order_status, query_product_info]