import json
from __004__langgraph_more_nodes.agent_state import AgentState
from common.llm import my_llm
from langchain_core.messages import HumanMessage


def catalog_check_tool(state: AgentState) -> dict:
    """
    医保目录判定工具。
    查询药品/诊疗项目是否在医保目录、甲乙类分类、报销限制，返回结构化结果。
    """
    print("开始医保目录判定")
    user_input = state["input"]
    matched_medicines = state.get("matched_medicines", [])
    matched_treat_items = state.get("matched_treat_items", [])
    cypher_results = state.get("cypher_results", [])

    prompt = f"""
你是一个医保目录判定工具。

【用户问题】
{user_input}

【匹配的实体】
- 药品: {json.dumps(matched_medicines, ensure_ascii=False)}
- 诊疗项目: {json.dumps(matched_treat_items, ensure_ascii=False)}

【图谱查询结果】
{json.dumps(cypher_results, ensure_ascii=False, indent=2)}

请根据以上信息，判定药品/诊疗项目是否在医保目录内。

输出JSON格式：
{{
    "items": [
        {{
            "name": "药品/项目名称",
            "in_catalog": true/false,
            "catalog_type": "甲类/乙类/丙类/不在目录",
            "reimburse_limit": "报销限制说明",
            "remark": "备注"
        }}
    ]
}}

注意：只能输出JSON，不要输出其他任何内容。
"""

    response = my_llm.invoke([HumanMessage(content=prompt)])
    raw_output = response.content.strip()

    try:
        catalog_result = json.loads(raw_output)
    except json.JSONDecodeError:
        catalog_result = {"raw_output": raw_output, "error": "解析失败"}

    print(f"完成医保目录判定")
    return {
        "tool_result": catalog_result,
        "tool_type": "catalog_check"
    }


if __name__ == '__main__':
    state = AgentState(
        input="二甲双胍在医保目录里吗？",
        matched_medicines=["二甲双胍"],
        matched_treat_items=[],
        cypher_results=[]
    )
    result = catalog_check_tool(state)
    print(result)
