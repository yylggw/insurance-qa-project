import json
from __004__langgraph_more_nodes.agent_state import AgentState
from langchain_core.messages import HumanMessage
from common.llm import my_llm


def intent_route_node(state: AgentState) -> dict:
    """
    全局意图识别总路由节点。
    结合对话历史做指代消解，同时判断：
    1. 是否有小红书/内容发布意图
    2. 是否为医保业务相关问题
    """
    print("开始全局意图识别")
    user_input = state["input"]
    history = state.get("history_messages", [])

    # 构建历史上下文
    history_str = ""
    if history:
        history_str = "对话历史：\n" + "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in history[-5:]]
        )

    prompt = f"""
{history_str}

用户当前输入: {user_input}

你是一个意图分类器，请判断以下两个维度（输出严格JSON格式）：

1. is_xiaohongshu_publish_intent: 用户是否有在小红书/社交平台发布内容的意图
   （关键词：发笔记、发小红书、写文章、生成文案、配图发布等）

2. is_insurance_intent: 用户输入是否与医保政策相关
   【医保知识图谱范围】
   - 疾病病种 (Disease)：如高血压、糖尿病、肺恶性肿瘤等
   - 药品 (Medicine)：包括药品名称、剂型、规格、医保类别等
   - 诊疗项目 (TreatItem)：如血常规检查、血液透析、冠状动脉支架植入术等
   - 参保类型 (InsureType)：如职工基本医疗保险、城乡居民基本医疗保险、大病保险等
   - 政策文件 (PolicyDoc)：如《国家基本医疗保险药品目录》《门诊慢特病保障方案》等
   - 报销规则 (ReimburseRule)：如高血压门诊报销规则、冠心病住院报销规则等
   - 经办机构 (Agency)：如各地医疗保险事务管理中心等

输出JSON格式：
{{
    "is_xiaohongshu_publish_intent": true/false,
    "is_insurance_intent": true/false
}}

注意：只能输出JSON，不要输出其他任何内容。
"""

    response = my_llm.invoke([HumanMessage(content=prompt)])
    raw_output = response.content.strip()

    try:
        result = json.loads(raw_output)
        is_xiaohongshu = result.get("is_xiaohongshu_publish_intent", False)
        is_insurance = result.get("is_insurance_intent", False)
    except json.JSONDecodeError:
        # 兜底：如果大模型没有返回JSON，用简单规则判断
        is_xiaohongshu = any(kw in user_input for kw in ["小红书", "发笔记", "发内容", "写文章", "生成文案"])
        is_insurance = any(kw in user_input for kw in ["医保", "报销", "药品目录", "参保", "门诊", "住院", "慢特病"])

    print(f"完成全局意图识别: 发布意图={is_xiaohongshu}, 医保意图={is_insurance}")
    return {
        "is_xiaohongshu_publish_intent": is_xiaohongshu,
        "is_insurance_intent": is_insurance
    }


if __name__ == '__main__':
    state = AgentState(input="高血压门诊报销比例是多少？", history_messages=[])
    result = intent_route_node(state)
    print(result)
