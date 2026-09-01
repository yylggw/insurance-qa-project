import json
from __004__langgraph_more_nodes.agent_state import AgentState


def faiss_result_sort_node(state: AgentState) -> dict:
    """
    对FAISS召回文档做去重、排序、截断，提取核心政策要点。
    """
    print("开始整理FAISS向量检索结果")
    retrieved_docs = state.get("retrieved_docs", [])

    if not retrieved_docs:
        print("FAISS检索结果为空")
        return {
            "retrieved_docs": [],
            "faiss_result_text": "未检索到相关政策文档"
        }

    # 按相似度降序排序
    sorted_docs = sorted(retrieved_docs, key=lambda x: x.get("similarity", 0), reverse=True)

    # 去重（基于文本内容）
    seen_texts = set()
    unique_docs = []
    for doc in sorted_docs:
        text = doc.get("text", "")
        if text not in seen_texts:
            seen_texts.add(text)
            unique_docs.append(doc)

    # 截断：只保留Top3
    top_docs = unique_docs[:3]

    # 生成可读文本
    result_text = "\n\n".join([
        f"[相似度: {doc['similarity']:.2f}]\n{doc['text']}"
        for doc in top_docs
    ])

    print(f"完成FAISS结果整理，保留{len(top_docs)}条文档")
    return {
        "retrieved_docs": top_docs,
        "faiss_result_text": result_text
    }


if __name__ == '__main__':
    state = AgentState(
        retrieved_docs=[
            {"text": "高血压门诊报销比例为70%", "similarity": 0.92},
            {"text": "高血压门诊报销比例为70%", "similarity": 0.88},
            {"text": "糖尿病门诊报销比例为65%", "similarity": 0.75}
        ]
    )
    result = faiss_result_sort_node(state)
    print(result.get("faiss_result_text"))
