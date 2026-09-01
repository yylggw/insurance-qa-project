from __004__langgraph_more_nodes.agent_state import AgentState
from common.llm import my_llm
from langchain_core.messages import HumanMessage


def content_revise_node(state: AgentState) -> dict:
    """
    按意见修改文案节点。
    合规校验不通过时，根据反馈意见调整重写文案。
    """
    print("开始修改文案")
    user_input = state["input"]
    current_title = state.get("xiaohongshu_post_title", "")
    current_content = state.get("xiaohongshu_post_content", "")
    revise_reason = state.get("revise_reason", "内容需要优化")

    prompt = f"""
你是一个医保科普内容修改助手。

原始文案：
标题：{current_title}
正文：{current_content}

修改原因：{revise_reason}

用户需求：{user_input}

请根据修改原因重新生成文案，要求：
1. 标题不超过19个中文字符，简短有吸引力
2. 正文具有分享性和实用性，语气自然亲切
3. 内容准确，符合医保政策

输出JSON格式：
{{
    "title": "新标题",
    "content": "新正文"
}}

注意：只能输出JSON，不要输出其他任何内容。
"""

    response = my_llm.invoke([HumanMessage(content=prompt)])
    raw_output = response.content.strip()

    import json
    try:
        result = json.loads(raw_output)
        new_title = result.get("title", current_title)
        new_content = result.get("content", current_content)
    except json.JSONDecodeError:
        new_title = current_title
        new_content = current_content

    print(f"完成文案修改")
    return {
        "xiaohongshu_post_title": new_title,
        "xiaohongshu_post_content": new_content,
        "content_revise_times": state.get("content_revise_times", 0) + 1
    }


if __name__ == '__main__':
    state = AgentState(
        input="写一篇文章，关于医保报销流程。",
        xiaohongshu_post_title="医保报销",
        xiaohongshu_post_content="医保报销流程很简单",
        revise_reason="内容太简短，需要补充详细信息"
    )
    result = content_revise_node(state)
    print(result)
