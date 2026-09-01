from __004__langgraph_more_nodes.agent_state import AgentState
from langchain_core.messages import HumanMessage, AIMessage
from common.llm import my_llm


def llm_direct_out_node(state: AgentState):
    print("开始生成直接用户回答")
    # 获取用户输入
    user_input = state["input"]

    # 构建提示词（闲聊兜底）
    prompt = f"""
    用户输入: {user_input}

    你是医保政策智能问答助手（基政易答）的闲聊兜底角色。  
    要求：
    - 如果问题与医保无关，请给出简洁、友好的常规回答，并提醒用户可以咨询医保相关问题。  
    - 回答要准确、简洁，避免无关内容。  
    - 输出时只给出最终答案，不要解释你是如何推理的。
    """

    # 携带最近几轮对话历史调用大模型，实现多轮记忆
    history_messages = state.get("history_messages", [])
    messages = []
    for msg in history_messages[-10:]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=prompt))

    response = my_llm.invoke(messages)
    model_answer = response.content.strip()
    # 将本轮问答追加到历史记录（user + assistant 成对），并限制长度避免无限增长
    history_messages.append({"role": "user", "content": user_input})
    history_messages.append({"role": "assistant", "content": model_answer})
    history_messages = history_messages[-20:]
    # 把历史记录更新到state中的history_messages字段中
    state["history_messages"] = history_messages

    # 存入 state
    state["direct_out"] = model_answer
    state["output"] = model_answer
    print("完成生成直接用户回答")
    return state