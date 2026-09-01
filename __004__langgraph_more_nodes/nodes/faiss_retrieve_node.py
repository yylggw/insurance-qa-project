import faiss
import pickle
from __004__langgraph_more_nodes.agent_state import AgentState
from common.config import Config
from common.embedding_model import embedding_model

conf = Config()

# 加载FAISS索引和映射
index = faiss.read_index(conf.ENTITY_INDEX_PATH)
with open(conf.ENTITY_ID2TEXT_PATH, "rb") as f:
    id2text = pickle.load(f)


def faiss_retrieve_node(state: AgentState) -> dict:
    """
    图谱查询失败/无结果/重试超限时触发。
    召回Top3相关政策文档存入 retrieved_docs。
    """
    print("开始FAISS向量检索降级")
    user_input = state["input"]

    # 生成查询向量
    query_emb = embedding_model.encode(
        [user_input], convert_to_numpy=True, normalize_embeddings=True
    )

    # 检索Top5
    dists, ids = index.search(query_emb, 5)

    retrieved_docs = []
    for j, i in enumerate(ids[0]):
        if i == -1:
            continue
        dist = dists[0][j]
        sim = 1.0 - dist / 2.0
        retrieved_docs.append({
            "text": id2text[i],
            "similarity": float(sim)
        })

    print(f"完成FAISS向量检索，召回{len(retrieved_docs)}条文档")
    return {
        "retrieved_docs": retrieved_docs
    }


if __name__ == '__main__':
    state = AgentState(input="高血压门诊报销比例是多少？")
    result = faiss_retrieve_node(state)
    print(result)
