import json
from __004__langgraph_more_nodes.agent_state import AgentState
from langchain_core.messages import HumanMessage
from common.llm import my_llm


def entity_and_intent_node(state: AgentState) -> dict:
    """
    实体抽取 + 细意图分类节点。
     抽取6类医保实体存入 user_input_* 字段
    ② 识别细意图：图谱查询类、报销测算类、目录查询类、待遇对比类、办事流程类
    """
    print("开始实体抽取与细意图分类")
    user_input = state["input"]
    history_messages = state.get("history_messages", [])

    # 构建最近几轮对话历史，用于追问/指代类问题的实体还原
    history_str = ""
    if history_messages:
        history_str = "【对话历史】\n" + "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in history_messages[-10:]]
        ) + "\n"

    prompt = f"""
你是一个医保知识图谱的实体抽取与意图分类助手。

{history_str}请结合对话历史，从以下用户输入中完成两个任务（如输入中存在“它/这个/该病”等指代，
请从对话历史中还原所指实体后再抽取）：

任务一：抽取六类实体
1. diseases（疾病病种），如高血压、糖尿病、肺恶性肿瘤等
2. medicines（药品），如阿莫西林、二甲双胍、奥希替尼等
3. treat_items（诊疗项目），如血常规检查、血液透析、冠状动脉支架植入术等
4. insure_types（参保类型），如职工基本医疗保险、城乡居民基本医疗保险、大病保险等
5. policy_docs（政策文件），如《国家基本医疗保险药品目录》等
6. rules（报销规则），如高血压门诊报销规则、冠心病住院报销规则等

任务二：识别细意图类型（五选一）
- graph_query: 图谱查询类（查询疾病、药品、诊疗项目、参保类型、政策文件、报销规则的具体信息）
- reimburse_calc: 报销测算类（涉及具体费用计算、报销金额、自付金额等）
- catalog_check: 目录查询类（查询某药品/诊疗项目是否在医保目录内、甲乙类分类等）
- benefit_compare: 待遇对比类（对比不同参保类型、不同病种的报销待遇差异）
- process_guide: 办事流程类（如何办理、需要什么材料、去哪里办等流程性问题）

输出严格JSON格式：
{{
    "diseases": ["..."],
    "medicines": ["..."],
    "treat_items": ["..."],
    "insure_types": ["..."],
    "policy_docs": ["..."],
    "rules": ["..."],
    "sub_intent": "graph_query|reimburse_calc|catalog_check|benefit_compare|process_guide"
}}

用户输入：{user_input}

注意：只能输出JSON，不要输出其他任何内容。
"""

    response = my_llm.invoke([HumanMessage(content=prompt)])
    raw_output = response.content.strip()

    try:
        result = json.loads(raw_output)
    except json.JSONDecodeError:
        result = {
            "diseases": [], "medicines": [], "treat_items": [],
            "insure_types": [], "policy_docs": [], "rules": [],
            "sub_intent": "graph_query"
        }

    sub_intent = result.get("sub_intent", "graph_query")
    print(f"完成实体抽取与细意图分类: sub_intent={sub_intent}")

    return {
        "user_input_diseases": result.get("diseases", []),
        "user_input_medicines": result.get("medicines", []),
        "user_input_treat_items": result.get("treat_items", []),
        "user_input_insure_types": result.get("insure_types", []),
        "user_input_policy_docs": result.get("policy_docs", []),
        "user_input_rules": result.get("rules", []),
        "sub_intent": sub_intent
    }


if __name__ == '__main__':
    state = AgentState(input="高血压门诊报销比例是多少？用的药是二甲双胍，属于职工医保。")
    result = entity_and_intent_node(state)
    print(result)
