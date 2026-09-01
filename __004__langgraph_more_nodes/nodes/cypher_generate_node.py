import faiss
import pickle
import json
from __004__langgraph_more_nodes.agent_state import AgentState
from common.config import Config
from common.embedding_model import embedding_model
from common.llm import my_llm
from langchain_core.messages import HumanMessage

conf = Config()

# 加载FAISS索引和映射
index = faiss.read_index(conf.ENTITY_INDEX_PATH)
with open(conf.ENTITY_ID2TEXT_PATH, "rb") as f:
    id2text = pickle.load(f)


def search_faiss(query, top_k=3, threshold=0.85):
    """在FAISS索引中搜索，返回相似度高于阈值的实体文本列表"""
    query_emb = embedding_model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    dists, ids = index.search(query_emb, top_k)
    results = []
    for j, i in enumerate(ids[0]):
        if i == -1:
            continue
        dist = dists[0][j]
        sim = 1.0 - dist / 2.0
        if sim >= threshold:
            results.append({"text": id2text[i], "similarity": float(sim)})
    return [r['text'] for r in results]


def cypher_generate_node(state: AgentState) -> dict:
    """
    ① 通过FAISS将口语化实体对齐到图谱标准实体，存入 matched_* 字段
    ② 结合图谱Schema生成Cypher语句存入 cypher_query
     首次进入初始化 cypher_retry_times 为0
    """
    print("开始FAISS实体匹配与Cypher生成")

    # 1. FAISS实体匹配
    user_input_diseases = state.get("user_input_diseases", [])
    user_input_medicines = state.get("user_input_medicines", [])
    user_input_treat_items = state.get("user_input_treat_items", [])
    user_input_insure_types = state.get("user_input_insure_types", [])
    user_input_policy_docs = state.get("user_input_policy_docs", [])
    user_input_rules = state.get("user_input_rules", [])

    matched_diseases, matched_medicines, matched_treat_items = [], [], []
    matched_insure_types, matched_policy_docs, matched_rules = [], [], []

    for dis in user_input_diseases:
        matched_diseases.extend(search_faiss(dis))
    for med in user_input_medicines:
        matched_medicines.extend(search_faiss(med))
    for item in user_input_treat_items:
        matched_treat_items.extend(search_faiss(item))
    for ins in user_input_insure_types:
        matched_insure_types.extend(search_faiss(ins))
    for doc in user_input_policy_docs:
        matched_policy_docs.extend(search_faiss(doc))
    for rule in user_input_rules:
        matched_rules.extend(search_faiss(rule))

    # 去重
    matched_diseases = list(set(matched_diseases))
    matched_medicines = list(set(matched_medicines))
    matched_treat_items = list(set(matched_treat_items))
    matched_insure_types = list(set(matched_insure_types))
    matched_policy_docs = list(set(matched_policy_docs))
    matched_rules = list(set(matched_rules))

    # 2. 构建匹配实体信息
    matched_info = {
        "diseases": matched_diseases,
        "medicines": matched_medicines,
        "treat_items": matched_treat_items,
        "insure_types": matched_insure_types,
        "policy_docs": matched_policy_docs,
        "rules": matched_rules
    }

    # 3. 生成Cypher语句
    kg_metadata = conf.KG_METADATA
    user_input = state["input"]

    prompt = f"""
你是一个医保知识图谱的Cypher查询生成专家。

【知识图谱元数据】
{kg_metadata}

【用户问题】
{user_input}

【已匹配的图谱标准实体】
{json.dumps(matched_info, ensure_ascii=False, indent=2)}

请根据以上信息，生成1~3条Cypher查询语句来回答用户问题。

要求：
1. 只输出JSON数组格式，每条Cypher语句作为数组元素
2. 使用MATCH语句，不要使用CREATE/DELETE等修改语句
3. 节点标签使用：Disease, Medicine, TreatItem, InsureType, PolicyDoc, ReimburseRule, Agency
4. 如果匹配的实体为空，尝试用用户输入中的关键词构造查询

输出格式：
["Cypher语句1", "Cypher语句2"]

注意：只能输出JSON数组，不要输出其他任何内容。
"""

    response = my_llm.invoke([HumanMessage(content=prompt)])
    raw_output = response.content.strip()

    try:
        cypher_list = json.loads(raw_output)
        if not isinstance(cypher_list, list):
            cypher_list = [raw_output]
    except json.JSONDecodeError:
        cypher_list = [raw_output]

    print(f"完成FAISS实体匹配与Cypher生成，生成{len(cypher_list)}条Cypher语句")

    return {
        "matched_diseases": matched_diseases,
        "matched_medicines": matched_medicines,
        "matched_treat_items": matched_treat_items,
        "matched_insure_types": matched_insure_types,
        "matched_policy_docs": matched_policy_docs,
        "matched_rules": matched_rules,
        "cypher_query": cypher_list,
        "cypher_retry_times": 0,
        "is_all_validate_cypher": True  # 默认合法，由check节点验证
    }


if __name__ == '__main__':
    state = AgentState(
        input="高血压门诊报销比例是多少？",
        user_input_diseases=["高血压"],
        user_input_medicines=[],
        user_input_treat_items=[],
        user_input_insure_types=["职工医保"],
        user_input_policy_docs=[],
        user_input_rules=[]
    )
    result = cypher_generate_node(state)
    print(result)
