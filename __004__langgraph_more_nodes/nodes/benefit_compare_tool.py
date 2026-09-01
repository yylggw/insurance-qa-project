import json
from __004__langgraph_more_nodes.agent_state import AgentState
from common.llm import my_llm
from langchain_core.messages import HumanMessage


def benefit_compare_tool(state: AgentState) -> dict:
    """
    参保待遇对比工具。
    对比不同参保类型/病种的报销待遇差异，输出结构化对比结果。
    """
    print("开始参保待遇对比")
    user_input = state["input"]
    matched_insure_types = state.get("matched_insure_types", [])
    matched_diseases = state.get("matched_diseases", [])
    cypher_results = state.get("cypher_results", [])

    prompt = f"""
你是一个医保待遇对比工具。

【用户问题】
{user_input}

【匹配的实体】
- 参保类型: {json.dumps(matched_insure_types, ensure_ascii=False)}
- 疾病: {json.dumps(matched_diseases, ensure_ascii=False)}

【图谱查询结果】
{json.dumps(cypher_results, ensure_ascii=False, indent=2)}

请根据以上信息，对比不同参保类型或病种的报销待遇差异。

输出JSON格式：
{{
    "comparison": [
        {{
            "insure_type": "参保类型",
            "disease": "病种",
            "reimburse_ratio": "报销比例",
            "deductible": "起付线",
            "ceiling": "封顶线",
            "special_notes": "特殊说明"
        }}
    ],
    "summary": "对比总结"
}}

注意：只能输出JSON，不要输出其他任何内容。
"""

    response = my_llm.invoke([HumanMessage(content=prompt)])
    raw_output = response.content.strip()

    try:
        compare_result = json.loads(raw_output)
    except json.JSONDecodeError:
        compare_result = {"raw_output": raw_output, "error": "解析失败"}

    print(f"完成参保待遇对比")
    return {
        "tool_result": compare_result,
        "tool_type": "benefit_compare"
    }


if __name__ == '__main__':
    state = AgentState(
        input="职工医保和居民医保报销待遇有什么区别？",
        matched_insure_types=["职工基本医疗保险", "城乡居民基本医疗保险"],
        matched_diseases=[],
        cypher_results=[]
    )
    result = benefit_compare_tool(state)
    print(result)
