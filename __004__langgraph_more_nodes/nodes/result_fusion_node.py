import json
from __004__langgraph_more_nodes.agent_state import AgentState


def result_fusion_node(state: AgentState) -> dict:
    """
    多源结果融合 + 溯源标注节点。
    统一收口，整合图谱结果、向量结果、工具输出；
    提取信息来源存入 answer_sources，实现回答全链路可溯源。
    """
    print("开始多源结果融合")

    answer_sources = []
    fusion_context_parts = []

    # 1. 整合图谱查询结果
    graph_result_text = state.get("graph_result_text", "")
    if graph_result_text:
        fusion_context_parts.append(f"【图谱查询结果】\n{graph_result_text}")
        answer_sources.append("来源：Neo4j知识图谱结构化查询")

    # 2. 整合FAISS向量检索结果
    faiss_result_text = state.get("faiss_result_text", "")
    if faiss_result_text:
        fusion_context_parts.append(f"【向量检索结果】\n{faiss_result_text}")
        answer_sources.append("来源：FAISS向量相似度检索")

    # 3. 整合工具输出
    tool_result = state.get("tool_result")
    tool_type = state.get("tool_type", "")
    if tool_result:
        tool_text = json.dumps(tool_result, ensure_ascii=False, indent=2)
        fusion_context_parts.append(f"【工具计算结果】\n{tool_text}")
        tool_name_map = {
            "reimburse_calc": "报销金额测算工具",
            "catalog_check": "医保目录判定工具",
            "benefit_compare": "参保待遇对比工具"
        }
        source_name = tool_name_map.get(tool_type, tool_type)
        answer_sources.append(f"来源：{source_name}")

    # 4. 整合匹配实体信息
    matched_info = {}
    for key in ["matched_diseases", "matched_medicines", "matched_treat_items",
                "matched_insure_types", "matched_policy_docs", "matched_rules"]:
        values = state.get(key, [])
        if values:
            matched_info[key] = values
    if matched_info:
        fusion_context_parts.append(f"【匹配实体】\n{json.dumps(matched_info, ensure_ascii=False)}")

    fusion_context = "\n\n".join(fusion_context_parts)

    print(f"完成多源结果融合，共{len(answer_sources)}个信息源")
    return {
        "fusion_context": fusion_context,
        "answer_sources": answer_sources
    }


if __name__ == '__main__':
    state = AgentState(
        input="高血压门诊报销比例是多少？",
        graph_result_text='[{"query": "MATCH...", "status": "success", "data": [{"d": {"name": "高血压"}}]}]',
        faiss_result_text="",
        tool_result=None,
        matched_diseases=["高血压"],
        matched_medicines=[]
    )
    result = result_fusion_node(state)
    print(result.get("fusion_context"))
    print(result.get("answer_sources"))
