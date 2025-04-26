# 1. 加载文档
import os
from dotenv import load_dotenv
# 加载环境变量
load_dotenv()

from langchain_community.document_loaders import WebBaseLoader
loader = WebBaseLoader(
    web_paths=("https://zh.wikipedia.org/wiki/黑神话：悟空",)
)
docs = loader.load()

# 2. 文档分块
from langchain_text_splitters import RecursiveCharacterTextSplitter
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
all_splits = text_splitter.split_documents(docs)

# 3. 设置嵌入模型
from langchain_huggingface import HuggingFaceEmbeddings
embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-zh-v1.5",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

# 4. 创建向量存储
from langchain_core.vectorstores import InMemoryVectorStore
vector_store = InMemoryVectorStore(embeddings)
vector_store.add_documents(all_splits)

# 5. 定义RAG提示词
from langchain import hub
prompt = hub.pull("rlm/rag-prompt")

# 6. 定义应用状态 (State)
# State (使用 TypedDict 定义) 是 LangGraph 的核心概念之一。
# 它不是一个对象实例，而是一个数据结构的蓝图或模式 (Schema)。
# 它规定了在整个图 (Graph) 执行过程中，需要在不同节点间共享和传递哪些数据及其类型。
# LangGraph 内部维护一个遵循此结构的 *共享字典*，并在节点间传递和更新。
from typing import List
from typing_extensions import TypedDict
from langchain_core.documents import Document
import pprint # 导入 pprint 用于美化打印最终状态

class State(TypedDict):
    question: str           # 用户问题
    context: List[Document] # 检索到的文档
    answer: str             # 生成的答案

# 7. 定义检索节点 (retrieve)
# 每个节点函数接收当前的 *共享 State 字典* 作为输入。
def retrieve(state: State):
    print("--- [执行节点: retrieve] ---") # 简单打印，指示节点执行
    question = state["question"] # 从传入的 state 字典中读取所需数据
    retrieved_docs = vector_store.similarity_search(question)

    # 核心机制：节点函数返回一个包含其想要 *更新* 到共享 State 中的字段的 *部分字典*。
    # 它不需要返回完整的 State，只需返回它产生的新数据。
    # LangGraph 会自动将这个返回的字典合并 (merge) 回共享 State 字典中。
    return {"context": retrieved_docs} # 返回包含新 context 的字典

# 8. 定义生成节点 (generate)
# 这个节点同样接收当前的共享 State 字典 (此时应已包含由 retrieve 更新的 context)。
def generate(state: State):
    print("--- [执行节点: generate] ---") # 简单打印，指示节点执行
    from langchain_ollama import ChatOllama
    llm = ChatOllama(model=os.getenv("OLLAMA_MODEL"), base_url="http://127.0.0.1:11434")

    # 从 state 字典读取所需数据
    question = state["question"]
    context_docs = state["context"]
    docs_content = "\n\n".join(doc.page_content for doc in context_docs)

    # 执行节点的主要逻辑
    messages = prompt.invoke({"question": question, "context": docs_content})
    response = llm.invoke(messages)

    # 返回包含新生成的 answer 的部分字典，用于更新共享 State
    return {"answer": response.content}

# 9. 构建和编译应用 (Graph)
from langgraph.graph import START, StateGraph # pip install langgraph
graph_builder = StateGraph(State) # 初始化 StateGraph，告知其状态蓝图

# 添加节点：将函数与图中的逻辑单元（节点）关联起来
graph_builder.add_node("retrieve", retrieve)
graph_builder.add_node("generate", generate)

# 定义边：指定节点间的执行顺序
graph_builder.add_edge(START, "retrieve")      # 图的执行从 START 开始，流向 "retrieve" 节点
graph_builder.add_edge("retrieve", "generate") # "retrieve" 节点执行完毕后，流向 "generate" 节点

# 编译图：将定义的节点和边构建成一个可运行的应用
graph = graph_builder.compile()

# 10. 运行查询
question = "黑悟空有哪些游戏场景？"
# 调用 invoke 时，传入一个字典来 *初始化* 共享 State 的起始值。
# 这里我们用问题初始化 "question" 字段。
print(f"\n=== 开始执行 graph.invoke (初始输入: {{'question': '{question}'}}) ===")
# invoke 会驱动整个图的执行，共享 State 会在节点间流动并被更新
response = graph.invoke({"question": question})
print("\n=== graph.invoke 执行完毕 ===")

# 11. 打印最终结果
# invoke 的返回值是图执行完毕后，*最终* 的共享 State 字典，包含了所有节点更新的结果。
print("\n--- 最终返回的 State 字典 ---")
pprint.pprint(response)
print("--- 结束最终 State ---")

print(f"\n问题: {question}")
print(f"答案: {response['answer']}") # 从最终状态字典中提取所需的字段
