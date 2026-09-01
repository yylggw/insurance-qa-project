import json
from __004__langgraph_more_nodes.agent_state import AgentState
from common.llm import my_llm
from common.config import Config
from langchain_core.messages import HumanMessage

conf = Config()


def cypher_fix_node(state: AgentState) -> dict:
    """
    Cypher校验不通过时，根据错误信息调用大模型修正语句。
    cypher_retry_times 加1，更新 cypher_query。
    """
    print("开始修正Cypher语句")
    user_input = state["input"]
    cypher_query = state.get("cypher_query", [])
    retry_times = state.get("cypher_retry_times", 0) + 1
    kg_metadata = conf.KG_METADATA

    # 收集上一次校验的错误信息
    error_info = state.get("cypher_error_info", "Cypher语法校验未通过")

    prompt = f"""
你是一个医保知识图谱的Cypher查询修正专家。

【知识图谱元数据】
{kg_metadata}

【用户问题】
{user_input}

【上一轮生成的Cypher语句】
{json.dumps(cypher_query, ensure_ascii=False)}

【错误信息】
{error_info}

请根据错误信息修正Cypher语句，要求：
1. 只输出JSON数组格式
2. 使用MATCH语句，不要使用CREATE/DELETE等修改语句
3. 节点标签使用：Disease, Medicine, TreatItem, InsureType, PolicyDoc, ReimburseRule, Agency

输出格式：
["修正后的Cypher语句1", "修正后的Cypher语句2"]

注意：只能输出JSON数组，不要输出其他任何内容。
"""

    response = my_llm.invoke([HumanMessage(content=prompt)])
    raw_output = response.content.strip()

    try:
        cypher_list = json.loads(raw_output)
        if not isinstance(cypher_list, list):
            cypher_list = [raw_output]
    except json.JSONDecodeError:
        cypher_list = [raw_output]

    print(f"完成Cypher修正，重试次数={retry_times}，生成{len(cypher_list)}条语句")

    return {
        "cypher_query": cypher_list,
        "cypher_retry_times": retry_times,
        "is_all_validate_cypher": True  # 修正后默认合法，由check节点再次验证
    }


if __name__ == '__main__':
    state = AgentState(
        input="高血压门诊报销比例是多少？",
        cypher_query=["MATCH (d:Disease {name:'高血压'}) RETURN d"],
        cypher_retry_times=0,
        cypher_error_info="语法错误"
    )
    result = cypher_fix_node(state)
    print(result)
