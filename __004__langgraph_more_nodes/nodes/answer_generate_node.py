from __004__langgraph_more_nodes.agent_state import AgentState
from common.llm import my_llm
from langchain_core.messages import HumanMessage


def answer_generate_node(state: AgentState) -> dict:
    """
    基于融合上下文+溯源信息，调用大模型生成通顺严谨的最终回答，存入 output。
    """
    print("开始生成最终回答")
    user_input = state["input"]
    fusion_context = state.get("fusion_context", "")
    answer_sources = state.get("answer_sources", [])
    history_messages = state.get("history_messages", [])

    sources_str = "\n".join([f"- {s}" for s in answer_sources]) if answer_sources else "无明确来源"

    # 构建最近几轮对话历史，支持追问/指代类多轮问题
    history_str = ""
    if history_messages:
        history_str = "【对话历史】\n" + "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in history_messages[-10:]]
        )

    prompt = f"""
你是一个医保政策问答助手（基政易答）。

{history_str}

【用户问题】
{user_input}

【参考信息】
{fusion_context if fusion_context else "未检索到相关参考信息"}

【信息来源】
{sources_str}

请结合对话历史理解用户当前问题（如存在“它/这个/该病”等指代，请从历史中还原），
用简洁、清晰、自然的中文回答用户的问题。
要求：
1. 回答要准确、专业，基于参考信息
2. 如果参考信息无法回答问题，请如实告知
3. 在回答末尾标注信息来源
4. 不要编造不存在的数据

请直接输出回答内容。
"""

    response = my_llm.invoke([HumanMessage(content=prompt)])
    answer = response.content.strip()

    # 更新历史记录（user + assistant 成对），并限制长度避免无限增长
    history_messages.append({"role": "user", "content": user_input})
    history_messages.append({"role": "assistant", "content": answer})
    history_messages = history_messages[-20:]

    print("完成生成最终回答")
    return {
        "output": answer,
        "neo4j_answer": answer,
        "history_messages": history_messages
    }


if __name__ == '__main__':
    state = AgentState(
        input="高血压门诊报销比例是多少？",
        fusion_context="【图谱查询结果】\n高血压门诊报销比例为70%",
        answer_sources=["来源：Neo4j知识图谱结构化查询"]
    )
    result = answer_generate_node(state)
    print(result.get("output"))
