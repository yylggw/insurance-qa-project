import json
from __004__langgraph_more_nodes.agent_state import AgentState


def graph_result_sort_node(state: AgentState) -> dict:
    """
    清洗、去重、格式化Neo4j原始结果，整理为大模型易读的结构化内容。
    """
    print("开始整理图谱查询结果")
    cypher_results = state.get("cypher_results", [])

    sorted_results = []
    for item in cypher_results:
        query = item.get("query", "")
        result = item.get("result", [])
        error = item.get("error")

        if error:
            sorted_results.append({
                "query": query,
                "status": "error",
                "message": error
            })
            continue

        if not result:
            sorted_results.append({
                "query": query,
                "status": "empty",
                "message": "无结果"
            })
            continue

        # 清洗结果：提取关键信息
        cleaned = []
        for record in result:
            cleaned_record = {}
            for key, value in record.items():
                if isinstance(value, dict):
                    # 节点对象，提取所有属性
                    cleaned_record[key] = value
                else:
                    cleaned_record[key] = value
            cleaned.append(cleaned_record)

        sorted_results.append({
            "query": query,
            "status": "success",
            "data": cleaned
        })

    # 生成可读的结构化文本
    result_text = json.dumps(sorted_results, ensure_ascii=False, indent=2)
    print(f"完成图谱结果整理，共{len(sorted_results)}条")

    return {
        "cypher_results": sorted_results,
        "graph_result_text": result_text
    }


if __name__ == '__main__':
    state = AgentState(
        cypher_results=[
            {"query": "MATCH (d:Disease {name:'高血压'}) RETURN d",
             "result": [{"d": {"name": "高血压", "disease_code": "I10"}}],
             "error": None}
        ]
    )
    result = graph_result_sort_node(state)
    print(result.get("graph_result_text"))
