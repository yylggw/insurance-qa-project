import json
from __004__langgraph_more_nodes.agent_state import AgentState
from common.llm import my_llm
from langchain_core.messages import HumanMessage


def reimburse_calc_tool(state: AgentState) -> dict:
    """
    报销金额测算工具。
    根据参保类型、病种、总费用，结合图谱报销规则（起付线、比例、封顶线），
    计算报销金额、自付金额，返回结构化结果。
    """
    print("开始报销金额测算")
    user_input = state["input"]
    matched_diseases = state.get("matched_diseases", [])
    matched_insure_types = state.get("matched_insure_types", [])
    cypher_results = state.get("cypher_results", [])

    prompt = f"""
你是一个医保报销金额测算工具。

【用户问题】
{user_input}

【匹配的实体】
- 疾病: {json.dumps(matched_diseases, ensure_ascii=False)}
- 参保类型: {json.dumps(matched_insure_types, ensure_ascii=False)}

【图谱查询结果】
{json.dumps(cypher_results, ensure_ascii=False, indent=2)}

请根据以上信息，测算报销金额。如果图谱中有报销规则数据（起付线、报销比例、封顶线），请进行计算。

输出JSON格式：
{{
    "disease": "疾病名称",
    "insure_type": "参保类型",
    "total_cost": 总费用（如未提供则标注"需用户提供"）,
    "deductible": 起付线,
    "reimburse_ratio": 报销比例,
    "ceiling": 封顶线,
    "reimbursed_amount": 报销金额,
    "self_pay_amount": 自付金额,
    "calculation_detail": "计算过程说明"
}}

如果缺少必要数据（如总费用），请基于图谱规则给出计算公式。
注意：只能输出JSON，不要输出其他任何内容。
"""

    response = my_llm.invoke([HumanMessage(content=prompt)])
    raw_output = response.content.strip()

    try:
        calc_result = json.loads(raw_output)
    except json.JSONDecodeError:
        calc_result = {"raw_output": raw_output, "error": "解析失败"}

    print(f"完成报销金额测算")
    return {
        "tool_result": calc_result,
        "tool_type": "reimburse_calc"
    }


if __name__ == '__main__':
    state = AgentState(
        input="高血压门诊花了5000元，职工医保能报销多少？",
        matched_diseases=["高血压"],
        matched_insure_types=["职工基本医疗保险"],
        cypher_results=[{"query": "", "result": [{"r": {"rule_type": "门诊报销", "reimburse_ratio": "70%", "deductible": "500"}}], "error": None}]
    )
    result = reimburse_calc_tool(state)
    print(result)
