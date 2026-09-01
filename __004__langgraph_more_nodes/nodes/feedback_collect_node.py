from __004__langgraph_more_nodes.agent_state import AgentState


def feedback_collect_node(state: AgentState) -> dict:
    """
    用户反馈收集节点。
    回答末尾追加满意度反馈提示，记录本次问答关键信息，用于后续优化。
    """
    print("开始收集用户反馈")
    output = state.get("output", "")

    # 在回答末尾追加反馈提示
    feedback_prompt = "\n\n---\n💬 以上回答是否解决了您的问题？请回复「满意」或「不满意」，我们将持续优化服务。"

    # 记录本次问答关键信息
    qa_record = {
        "question": state.get("input", ""),
        "answer": output,
        "sources": state.get("answer_sources", []),
        "sub_intent": state.get("sub_intent", ""),
    }

    print("完成收集用户反馈")
    return {
        "output": output + feedback_prompt,
        "qa_record": qa_record
    }


if __name__ == '__main__':
    state = AgentState(
        input="高血压门诊报销比例是多少？",
        output="高血压门诊报销比例为70%。",
        answer_sources=["来源：Neo4j知识图谱结构化查询"],
        sub_intent="graph_query"
    )
    result = feedback_collect_node(state)
    print(result.get("output"))
