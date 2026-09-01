from __004__langgraph_more_nodes.agent_state import AgentState
from common.llm import my_llm
from langchain_core.messages import HumanMessage


def topic_confirm_node(state: AgentState) -> dict:
    """
    选题确认/主题输入节点。
    解析用户发布需求，明确内容主题、核心知识点。
    """
    print("开始选题确认")
    user_input = state["input"]

    prompt = f"""
你是一个医保科普内容策划助手。

用户想要发布医保相关内容，请根据以下输入明确内容主题和核心知识点：

用户输入：{user_input}

请输出JSON格式：
{{
    "topic": "内容主题（简洁概括）",
    "key_points": ["核心知识点1", "核心知识点2", "核心知识点3"],
    "target_audience": "目标受众"
}}

注意：只能输出JSON，不要输出其他任何内容。
"""

    response = my_llm.invoke([HumanMessage(content=prompt)])
    raw_output = response.content.strip()

    import json
    try:
        topic_info = json.loads(raw_output)
    except json.JSONDecodeError:
        topic_info = {
            "topic": user_input,
            "key_points": [],
            "target_audience": "普通大众"
        }

    print(f"完成选题确认: topic={topic_info.get('topic', '')}")
    return {
        "publish_topic": topic_info.get("topic", user_input),
        "publish_key_points": topic_info.get("key_points", []),
        "publish_target_audience": topic_info.get("target_audience", "普通大众")
    }


if __name__ == '__main__':
    state = AgentState(input="我想在小红书发一篇关于医保报销流程的笔记")
    result = topic_confirm_node(state)
    print(result)
