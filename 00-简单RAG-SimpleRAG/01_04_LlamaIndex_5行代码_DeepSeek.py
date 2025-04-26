# 第一行代码：导入相关的库
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
# from llama_index.llms.deepseek import DeepSeek # 如果直接调用官方 API，则使用 DeepSeek 类
from llama_index.llms.openai_like import OpenAILike # 使用 OpenAILike 适配中转站
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 加载本地嵌入模型
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-zh")

# 创建 OpenAILike LLM (通过中转站调用 DeepSeek 模型)
llm = OpenAILike(
    model="deepseek-ai/DeepSeek-V3-0324", # 修改为指定模型
    api_key=os.getenv("OPENAI_API_KEY"), # 从环境变量获取中转站 Key
    api_base=os.getenv("OPENAI_API_BASE"), # 从环境变量获取中转站 Base URL
    is_chat_model=True # 明确指定这是一个聊天模型
)

# 第二行代码：加载数据
documents = SimpleDirectoryReader(input_files=["90-文档-Data/黑悟空/黑悟空设定.txt"]).load_data()

# 第三行代码：构建索引
index = VectorStoreIndex.from_documents(
    documents,
    embed_model=embed_model
)

# 第四行代码：创建问答引擎
query_engine = index.as_query_engine(
    llm=llm
)

# 第五行代码: 开始问答
print(query_engine.query("黑神话悟空中有哪些战斗工具?"))
