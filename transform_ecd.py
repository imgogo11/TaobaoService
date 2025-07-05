import os

def transform_data(input_file, output_file):
    print(f"正在处理文件: {input_file}")
    count = 0
    with open(input_file, 'r', encoding='utf-8') as fin, \
         open(output_file, 'w', encoding='utf-8') as fout:
        
        for line in fin:
            try:
                parts = line.strip().split('\t')
                label = parts[0]
                
                # 我们只关心正确的对话样本
                if label == '1':
                    # 对话历史在中间，回复在最后
                    utterances = parts[1:-1]
                    response = parts[-1]
                    
                    # 启发式规则：如果对话历史不为空，取最后一句话当问题
                    if utterances:
                        question = utterances[-1]
                        
                        # 可以加一些简单的过滤，比如问题必须包含问号等
                        if '?' in question or '？' in question or '吗' in question or '什么' in question:
                            fout.write(f"Q: {question}\n")
                            fout.write(f"A: {response}\n\n")
                            count += 1
            except IndexError:
                # 忽略格式不正确的行
                continue
    print(f"处理完成！从 {input_file} 中提取了 {count} 个Q&A对，已保存至 {output_file}")

if __name__ == "__main__":
    if not os.path.exists("data"):
        os.makedirs("data")
        
    # 处理训练集
    transform_data("E-commerce dataset/train.txt", "data/faq_from_ecd_train.txt")
