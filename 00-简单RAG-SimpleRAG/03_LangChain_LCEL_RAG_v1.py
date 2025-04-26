# 1. 加载文档
from langchain_community.document_loaders import WebBaseLoader

loader = WebBaseLoader(
    web_paths=("https://zh.wikipedia.org/wiki/黑神话：悟空",)
)
docs = loader.load()

# 2. 分割文档
from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
all_splits = text_splitter.split_documents(docs)

# 3. 设置嵌入模型
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()

# 4. 创建向量存储
from langchain_core.vectorstores import InMemoryVectorStore

vectorstore = InMemoryVectorStore(embeddings)
vectorstore.add_documents(all_splits)

# 5. 创建检索器
# as_retriever 会创建一个 LangChain Runnable 对象，其输入是字符串（问题），输出是文档列表
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 6. 创建提示模板
from langchain_core.prompts import ChatPromptTemplate

# 模板需要 'context' 和 'question' 两个输入变量
prompt = ChatPromptTemplate.from_template("""
基于以下上下文，回答问题。如果上下文中没有相关信息，
请说"我无法从提供的上下文中找到相关信息"。
上下文: {context}
问题: {question}
回答:""")

# 7. 设置语言模型和输出解析器
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

llm = ChatOpenAI(model="gpt-3.5-turbo")
output_parser = StrOutputParser()

# 8. 构建 LCEL 链
# 定义一个辅助函数来格式化检索到的文档列表为单个字符串
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# 构建链
# chain.invoke(question) 的输入（question 字符串）会作为字典 { } 步骤的输入
chain = (
    {
        # "context" 分支：
        # 1. 接收 chain.invoke 的输入（question 字符串）
        # 2. 将其传递给 retriever 进行检索
        # 3. retriever 输出文档列表
        # 4. 文档列表传递给 format_docs 进行格式化，输出单个字符串
        "context": retriever | format_docs,

        # "question" 分支：
        # 1. 同样接收 chain.invoke 的输入（question 字符串）
        # 2. RunnablePassthrough 将其原样传递出去
        "question": RunnablePassthrough()
    }
    # 字典 { } 步骤的输出是一个包含 "context" 和 "question" 两个键的新字典
    | prompt         # 将字典输入给提示模板进行格式化
    | llm            # 将格式化后的提示发送给 LLM
    | output_parser  # 将 LLM 的输出 (AIMessage) 解析为字符串
)

# 9. 执行查询
question = "黑悟空有哪些游戏场景？"
print("\n=== 开始执行 chain.invoke ===")
response = chain.invoke(question)
print("\n=== chain.invoke 执行完毕 ===")

# 10. 打印最终结果
print("\n最终响应:")
print(response)