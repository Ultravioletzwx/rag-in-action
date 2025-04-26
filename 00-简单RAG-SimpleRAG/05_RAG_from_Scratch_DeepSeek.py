# 1. 准备文档数据
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

docs = [
    "黑神话悟空的战斗如同武侠小说活过来一般，当金箍棒与妖魔碰撞时，火星四溅，招式行云流水。悟空可随心切换狂猛或灵动的战斗风格，一棒横扫千军，或是腾挪如蝴蝶戏花。",    
    "72变神通不只是变化形态，更是开启新世界的钥匙。化身飞鼠可以潜入妖魔巢穴打探军情，变作金鱼能够探索深海遗迹的秘密，每一种变化都是一段独特的冒险。",    
    "每场BOSS战都是一场惊心动魄的较量。或是与身躯庞大的九头蟒激战于瀑布之巅，或是在雷电交织的云海中与雷公电母比拼法术，招招险象环生。",    
    "驾着筋斗云翱翔在这片神话世界，瑰丽的场景令人屏息。云雾缭绕的仙山若隐若现，古老的妖兽巢穴中藏着千年宝物，月光下的古寺钟声回荡在山谷。",    
    "这不是你熟悉的西游记。当悟空踏上寻找身世之谜的旅程，他将遇见各路神仙妖魔。有的是旧识，如同样桀骜不驯的哪吒；有的是劲敌，如手持三尖两刃刀的二郎神。",    
    "作为齐天大圣，悟空的神通不止于金箍棒。火眼金睛可洞察妖魔真身，一个筋斗便是十万八千里。而这些能力还可以通过收集天外陨铁、悟道石等材料来强化升级。",    
    "世界的每个角落都藏着故事。你可能在山洞中发现上古大能的遗迹，云端天宫里寻得昔日天兵的宝库，或是在凡间集市偶遇卖人参果的狐妖。",    
    "故事发生在大唐之前的蛮荒世界，那时天庭还未定鼎三界，各路妖王割据称雄。这是一个神魔混战、群雄逐鹿的动荡年代，也是悟空寻找真相的起点。",    
    "游戏的音乐如同一首跨越千年的史诗。古琴与管弦交织出战斗的激昂，笛萧与木鱼谱写禅意空灵。而当悟空踏入重要场景时，古风配乐更是让人仿佛穿越回那个神话的年代。"
    ] 

# 2. 设置嵌入模型: 将文本转换为向量
# -----------------------------------
# 加载预训练的 Sentence Transformer 模型。
# 该模型内部会进行分词，然后通过 Transformer 网络处理，最后进行池化 (Pooling)，
# 最终将每个输入的文本字符串转换为一个固定维度的数值向量 (嵌入)。
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
# 对文档列表中的每个文档进行编码，得到嵌入向量。
# doc_embeddings 是一个 NumPy 数组，形状为 (文档数量, 嵌入维度)，例如 (9, 384)。
# 每一行代表一个文档的语义向量表示。
doc_embeddings = model.encode(docs)
print(f"文档向量维度: {doc_embeddings.shape}")

# 3. 创建向量存储: 构建可供快速检索的索引
# --------------------------------------
import faiss # pip install faiss-cpu
import numpy as np
# 获取嵌入向量的维度，用于初始化 Faiss 索引。
dimension = doc_embeddings.shape[1]
# 创建一个 Faiss 索引。IndexFlatL2 表示：
# - IndexFlat: 存储原始向量，进行精确但可能是暴力的搜索。
# - L2: 使用 L2 距离 (欧氏距离) 作为向量间相似度的度量标准。距离越小越相似。
index = faiss.IndexFlatL2(dimension)
# 将所有文档的嵌入向量添加到 Faiss 索引中。
# Faiss 需要 float32 类型的数据。
index.add(doc_embeddings.astype('float32'))
print(f"向量数据库中的文档数量: {index.ntotal}")

# 4. 执行相似度检索: 查找与问题最相关的文档
# ---------------------------------------
question = "黑神话悟空的战斗系统有什么特点?"
# 关键步骤：使用 *相同的* Sentence Transformer 模型将问题文本也转换为嵌入向量。
# 确保问题向量和文档向量在同一个语义空间中。
query_embedding = model.encode([question])[0]
# 在 Faiss 索引中搜索与查询向量 query_embedding 最相似的 k 个向量。
# - 第一个参数: 查询向量 (需要是 NumPy 数组，通常 float32)。
# - k=3: 指定返回最相似的 3 个结果。
# - 输出:
#   - distances: 查询向量与找到的 k 个向量之间的 L2 距离。
#   - indices: 找到的 k 个向量在原始添加到索引时的 *索引号* (位置)。
distances, indices = index.search(
    np.array([query_embedding]).astype('float32'), 
    k=3
)
# 使用 indices 中返回的索引号，从原始的 docs 列表中提取出对应的文本内容。
# indices[0] 包含了具体的索引号列表，例如 [5, 0, 2]。
context = [docs[idx] for idx in indices[0]]
print("\n检索到的相关文档:")
for i, doc in enumerate(context, 1):
    print(f"[{i}] {doc}")

# 5. 构建提示词
prompt = f"""根据以下参考信息回答问题，并给出信息源编号。
如果无法从参考信息中找到答案，请说明无法回答。
参考信息:
{chr(10).join(f"[{i+1}] {doc}" for i, doc in enumerate(context))}
问题: {question}
答案:"""

# 6. 使用DeepSeek生成答案
from openai import OpenAI
client = OpenAI(
    # api_key=os.getenv("DEEPSEEK_API_KEY"), # 原始 DeepSeek API Key 的环境变量名
    api_key=os.getenv("OPENAI_API_KEY"), # 从环境变量获取中转站 Key
    # base_url="https://api.deepseek.com/v1" # 原始直接调用 DeepSeek API 的 Base URL
    base_url=os.getenv("OPENAI_API_BASE") # 从环境变量获取中转站 Base URL
)

response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V3-0324", # 修改为指定模型
    messages=[{
        "role": "user",
        "content": prompt
    }],
    max_tokens=1024
)
print(f"\n生成的答案: {response.choices[0].message.content}")
