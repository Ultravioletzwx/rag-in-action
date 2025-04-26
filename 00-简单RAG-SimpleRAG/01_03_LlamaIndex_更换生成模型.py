# 导入相关的库
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.embeddings.huggingface import HuggingFaceEmbedding # 需要pip install llama-index-embeddings-huggingface
# from llama_index.llms.deepseek import DeepSeek  # 使用 DeepSeek 类，如果直接调用官方 API
from llama_index.llms.openai_like import OpenAILike # 改为使用 OpenAILike 类来适配中转站

from llama_index.core import Settings # 可以看看有哪些Setting
# https://docs.llamaindex.ai/en/stable/examples/llm/deepseek/
# Settings.llm = DeepSeek(model="deepseek-chat")
Settings.embed_model = HuggingFaceEmbedding("BAAI/bge-small-zh")
# Settings.llm = OpenAI(model="gpt-3.5-turbo")
# Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")

# 加载环境变量
from dotenv import load_dotenv
import os

# 加载 .env 文件中的环境变量
load_dotenv()

# 创建 OpenAILike LLM（通过中转站调用 DeepSeek 模型）
llm = OpenAILike(
    model="deepseek-ai/DeepSeek-V3-0324",  # 使用中转台提供的模型名称
    api_key=os.getenv("OPENAI_API_KEY"),  # 从环境变量获取中转台的Key
    api_base=os.getenv("OPENAI_API_BASE"), # 从环境变量获取中转台的Base URL
    is_chat_model=True # 明确指定这是一个聊天模型
)

# 加载数据
documents = SimpleDirectoryReader(input_files=["90-文档-Data/黑悟空/黑悟空设定.txt"]).load_data() 

# 构建索引
index = VectorStoreIndex.from_documents(
    documents,
    # llm=llm  # 设置构建索引时的语言模型（一般不需要）
)

# 创建问答引擎
query_engine = index.as_query_engine(
    llm=llm  # 设置生成模型
    )

# 开始问答
print(query_engine.query("黑神话悟空中有哪些战斗工具?"))