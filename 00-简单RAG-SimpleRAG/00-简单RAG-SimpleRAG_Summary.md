# 00-简单RAG-SimpleRAG 章节总结

本章主要介绍了使用不同的库（LlamaIndex, LangChain, LangGraph）以及从零开始构建基本的检索增强生成 (RAG) 应用的核心流程和关键组件配置。

## 1. 基础 RAG 流程

所有示例都遵循或体现了 RAG 的核心步骤：

1.  **加载 (Load):** 从数据源（本地文件、网页等）加载文档。
2.  **分割 (Split):** 将长文档分割成更小的、语义相关的块 (Chunks)。
3.  **嵌入 (Embed):** 使用嵌入模型将文本块转换为数值向量 (Embeddings)。
4.  **存储 (Store):** 将文本块及其嵌入向量存储到向量数据库/存储中，并建立索引。
5.  **检索 (Retrieve):** 接收用户问题，将其嵌入，然后在向量存储中查找最相似（相关）的文本块向量，并取回对应的文本块。
6.  **生成 (Generate):** 将用户问题和检索到的上下文文本块组合成一个提示 (Prompt)，发送给大型语言模型 (LLM) 生成最终答案。

## 2. LlamaIndex 实现 (`01_...` 系列文件)

展示了 LlamaIndex 的简洁和模块化特性。

**核心代码:**

*   **五行代码 RAG:** 体现了 LlamaIndex 的高度封装，通过 `VectorStoreIndex.from_documents()` 和 `index.as_query_engine()` 快速构建 RAG 应用。
    ```python
    # 示例 (结合加载)
    from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
    documents = SimpleDirectoryReader(input_files=["..."]).load_data()
    index = VectorStoreIndex.from_documents(documents)
    query_engine = index.as_query_engine()
    response = query_engine.query("你的问题")
    ```

**关键组件替换:**

*   **更换嵌入模型:** 通过设置 `embed_model` 参数或全局 `Settings`，可以轻松切换嵌入模型，例如使用 HuggingFace 模型。
    ```python
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-zh")
    # 在构建索引或全局设置中使用 embed_model
    index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)
    # 或
    # from llama_index.core import Settings
    # Settings.embed_model = embed_model
    ```
*   **更换生成模型 (LLM):** 通过在 `as_query_engine` 中设置 `llm` 参数或全局 `Settings`，可以切换 LLM。
    *   **DeepSeek (直接 API):**
        ```python
        # from llama_index.llms.deepseek import DeepSeek
        # llm = DeepSeek(model="deepseek-chat", api_key=os.getenv("DEEPSEEK_API_KEY"))
        ```
    *   **Ollama (本地):**
        ```python
        from llama_index.llms.ollama import Ollama
        llm = Ollama(model=os.getenv("OLLAMA_MODEL"), request_timeout=360.0)
        ```
    *   **使用中转站 (OpenAI 兼容 API):** 当中转站提供 OpenAI 兼容接口时，需要使用 `OpenAILike` 类，并配置 `api_key` 和 `api_base`。
        ```python
        from llama_index.llms.openai_like import OpenAILike
        llm = OpenAILike(
            model="中转站提供的模型名", # 例如 "deepseek-ai/DeepSeek-V3-0324"
            api_key=os.getenv("MIDDLE_CHANNEL_API_KEY"), # 使用中转站的 Key
            api_base=os.getenv("MIDDLE_CHANNEL_API_BASE"),# 使用中转站的 URL
            is_chat_model=True # 明确是聊天模型
        )
        query_engine = index.as_query_engine(llm=llm)
        ```

## 3. LangChain 实现 (`02_...`, `03_...` 系列文件)

展示了 LangChain 的组件化和 LCEL (LangChain Expression Language) 的灵活性。

**核心组件:**

*   **Loaders:** `WebBaseLoader` 用于加载网页内容。
*   **Splitters:** `RecursiveCharacterTextSplitter` 用于文本分块。
*   **Embeddings:** `HuggingFaceEmbeddings`, `OpenAIEmbeddings` 用于文本嵌入。
*   **VectorStores:** `InMemoryVectorStore` 作为简单的内存向量存储。
*   **Retrievers:** 通过 `vectorstore.as_retriever()` 创建。
*   **Prompts:** `ChatPromptTemplate` 用于构建提示。
*   **LLMs:** `ChatDeepSeek`, `ChatOpenAI`, `ChatOllama` 等用于与 LLM 交互。
*   **OutputParsers:** `StrOutputParser` 用于解析 LLM 输出为字符串。

**关键配置与技术:**

*   **更换 LLM:**
    *   **DeepSeek (直接 API):**
        ```python
        # from langchain_deepseek import ChatDeepSeek
        # llm = ChatDeepSeek(model="...", api_key=os.getenv("DEEPSEEK_API_KEY"))
        ```
    *   **Ollama (本地):**
        ```python
        from langchain_ollama import ChatOllama
        llm = ChatOllama(model=os.getenv("OLLAMA_MODEL"), base_url="http://127.0.0.1:11434")
        ```
    *   **OpenAI 或中转站 (OpenAI 兼容 API):** 使用 `ChatOpenAI` 类，配置 `model`, `openai_api_key`, 和 `openai_api_base`。
        ```python
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model="中转站提供的模型名或 OpenAI 模型名",
            openai_api_key=os.getenv("API_KEY"), # OpenAI Key 或中转站 Key
            openai_api_base=os.getenv("API_BASE") # OpenAI Base URL 或中转站 Base URL
        )
        ```
*   **LCEL (LangChain Expression Language):** `03_...` 文件展示了 LCEL 的强大之处，使用 `|` (管道符) 连接不同的 Runnable 组件。
    *   **`RunnablePassthrough()`:** 将输入原样传递到下一步。
    *   **字典 `{}`:** 用于并行执行分支，并将结果组合成字典传递给下一步。常用于同时准备 `context` 和 `question`。
        ```python
        # LCEL 链示例
        chain = (
            {
                "context": retriever | format_docs, # 检索并格式化上下文
                "question": RunnablePassthrough()   # 直接传递问题
            }
            | prompt                            # 组合输入到提示模板
            | llm                               # 发送给 LLM
            | StrOutputParser()                 # 解析输出
        )
        response = chain.invoke("你的问题")
        ```

## 4. LangGraph 实现 (`04_...` 系列文件)

引入了 LangGraph 来构建更复杂、带状态的应用，特别是 RAG 流程。

**核心概念:**

*   **`State` (状态):** 使用 `TypedDict` 定义，作为图中共享数据的蓝图/模式。LangGraph 内部维护一个遵循此结构的共享字典。
*   **节点 (Nodes):** Python 函数，接收当前的**共享 State 字典**作为输入。
*   **状态更新机制:** 节点函数执行任务后，返回一个**部分字典**，包含其想要更新到共享 State 的字段。LangGraph 负责将返回的字典合并回共享 State。
    ```python
    # 示例节点函数返回更新字典
    def retrieve(state: State):
        # ... 执行检索 ...
        retrieved_docs = ...
        return {"context": retrieved_docs} # 只返回要更新的 context
    ```
*   **图构建:** 使用 `StateGraph(State)` 初始化，`add_node()` 添加节点，`add_edge()` 定义节点间的执行流程（边）。
*   **`graph.compile()`:** 编译图定义。
*   **`graph.invoke()`:** 输入一个字典来**初始化** State 的起始值，执行图，并返回**最终**的 State 字典。

## 5. RAG from Scratch (`05_...` 系列文件)

展示了不依赖特定 RAG 框架，直接使用基础库手动实现 RAG 的过程。

**使用库:**

*   `sentence-transformers`: 用于文本嵌入。
*   `faiss-cpu`: 用于高效的向量相似性搜索。
*   `openai`: 用于直接调用 OpenAI 兼容的 API (包括 DeepSeek 官方 API 或中转站)。

**关键步骤:**

1.  使用 `SentenceTransformer` 的 `encode()` 获取文档和查询的嵌入向量。
2.  创建 `faiss.IndexFlatL2` 索引并将文档向量 `add()` 进去。
3.  使用 `index.search()` 进行相似度检索，获取相关文档的索引号。
4.  根据索引号取回原始文档文本作为上下文。
5.  构建包含上下文和问题的提示字符串。
6.  使用 `openai` 库的 `OpenAI` 客户端，配置 `api_key` 和 `base_url` (可指向 DeepSeek 官方或中转站)，调用 `client.chat.completions.create()` 获取 LLM 响应。

## 6. 关键配置：环境变量与中转站

贯穿本章的一个重要实践是使用 `.env` 文件和 `dotenv` 库来管理敏感信息（如 API Key）和配置（如 API Base URL）。

*   **`.env` 文件:** 存储 `KEY=VALUE` 格式的配置。
*   **`load_dotenv()`:** 在 Python 脚本开头调用，将 `.env` 文件中的变量加载到环境变量中。
*   **`os.getenv("KEY_NAME")`:** 在代码中读取环境变量。
*   **适配中转站:** 当使用提供 OpenAI 兼容 API 的中转站时：
    *   **LlamaIndex:** 使用 `OpenAILike` 类，配置 `api_key` 和 `api_base`。
    *   **LangChain:** 使用 `ChatOpenAI` 类，配置 `openai_api_key` 和 `openai_api_base`。
    *   **直接 `openai` 库:** 配置 `OpenAI` 客户端的 `api_key` 和 `base_url`。 