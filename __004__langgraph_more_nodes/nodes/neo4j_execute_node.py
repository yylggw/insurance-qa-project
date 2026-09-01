from __004__langgraph_more_nodes.agent_state import AgentState
from common.neo4j_manager import neo4j_client


def neo4j_execute_node(state: AgentState) -> dict:
    """
    调用Neo4j执行合法Cypher，原始结果存入 cypher_results。
    """
    print("开始执行Neo4j查询")
    cypher_query_list = state.get("cypher_query", [])
    query_results = []

    for cypher_query in cypher_query_list:
        try:
            result_list = neo4j_client.run_cypher(cypher_query)
            query_results.append({
                "query": cypher_query,
                "result": result_list,
                "error": None
            })
        except Exception as e:
            query_results.append({
                "query": cypher_query,
                "result": [],
                "error": str(e)
            })

    print(f"完成Neo4j查询，共{len(query_results)}条结果")
    return {
        "cypher_results": query_results
    }


if __name__ == '__main__':
    state = AgentState(
        input="高血压门诊报销比例是多少？",
        cypher_query=["MATCH (d:Disease {name:'高血压'}) RETURN d"]
    )
    result = neo4j_execute_node(state)
    print(result)
