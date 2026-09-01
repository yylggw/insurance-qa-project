from langgraph.constants import START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph

from __004__langgraph_more_nodes.agent_state import AgentState

# ========== 全局意图路由 ==========
from __004__langgraph_more_nodes.nodes.intent_route_node import intent_route_node

# ========== 医保问答 - 实体与意图 ==========
from __004__langgraph_more_nodes.nodes.entity_and_intent_node import entity_and_intent_node

# ========== 医保问答 - Cypher 链路 ==========
from __004__langgraph_more_nodes.nodes.cypher_generate_node import cypher_generate_node
from __004__langgraph_more_nodes.nodes.cypher_fix_node import cypher_fix_node
from __004__langgraph_more_nodes.nodes.neo4j_execute_node import neo4j_execute_node

# ========== 医保问答 - 降级检索 ==========
from __004__langgraph_more_nodes.nodes.faiss_retrieve_node import faiss_retrieve_node

# ========== 医保问答 - 结果整理 ==========
from __004__langgraph_more_nodes.nodes.graph_result_sort_node import graph_result_sort_node
from __004__langgraph_more_nodes.nodes.faiss_result_sort_node import faiss_result_sort_node

# ========== 医保问答 - 业务工具 ==========
from __004__langgraph_more_nodes.nodes.reimburse_calc_tool import reimburse_calc_tool
from __004__langgraph_more_nodes.nodes.catalog_check_tool import catalog_check_tool
from __004__langgraph_more_nodes.nodes.benefit_compare_tool import benefit_compare_tool

# ========== 医保问答 - 融合与回答 ==========
from __004__langgraph_more_nodes.nodes.result_fusion_node import result_fusion_node
from __004__langgraph_more_nodes.nodes.answer_generate_node import answer_generate_node
from __004__langgraph_more_nodes.nodes.feedback_collect_node import feedback_collect_node

# ========== 兜底回答 ==========
from __004__langgraph_more_nodes.nodes.llm_direct_out_node import llm_direct_out_node

# ========== 小红书发布链路（保留现有节点） ==========
from __004__langgraph_more_nodes.nodes.topic_confirm_node import topic_confirm_node
from __004__langgraph_more_nodes.nodes.platform_select_node import platform_select_node
from __004__langgraph_more_nodes.nodes.text_generate_node import text_generate_node
from __004__langgraph_more_nodes.nodes.content_revise_node import content_revise_node
from __004__langgraph_more_nodes.nodes.image_generate_node import image_generator_node
from __004__langgraph_more_nodes.nodes.check_text_image_node import check_text_image_node
from __004__langgraph_more_nodes.nodes.auto_publish_xiaohongshu_node import xiaohongshu_auto_publish_node
from __004__langgraph_more_nodes.nodes.generate_markdown_node import generate_markdown_node

from common.ouput_graph_utils import output_pic_graph
from common.path_utils import get_file_path


def build_graph():
    """构建完整的 LangGraph 医保智能 Agent 工作流"""
    graph = StateGraph(AgentState)

    # ==================== 注册所有节点 ====================

    # 全局入口
    graph.add_node("intent_route_node", intent_route_node)

    # 医保问答 - 实体与意图
    graph.add_node("entity_and_intent_node", entity_and_intent_node)

    # 医保问答 - Cypher 链路
    graph.add_node("cypher_generate_node", cypher_generate_node)
    graph.add_node("cypher_fix_node", cypher_fix_node)
    graph.add_node("neo4j_execute_node", neo4j_execute_node)

    # 医保问答 - 降级检索
    graph.add_node("faiss_retrieve_node", faiss_retrieve_node)

    # 医保问答 - 结果整理
    graph.add_node("graph_result_sort_node", graph_result_sort_node)
    graph.add_node("faiss_result_sort_node", faiss_result_sort_node)

    # 医保问答 - 业务工具
    graph.add_node("reimburse_calc_tool", reimburse_calc_tool)
    graph.add_node("catalog_check_tool", catalog_check_tool)
    graph.add_node("benefit_compare_tool", benefit_compare_tool)

    # 医保问答 - 融合与回答
    graph.add_node("result_fusion_node", result_fusion_node)
    graph.add_node("answer_generate_node", answer_generate_node)
    graph.add_node("feedback_collect_node", feedback_collect_node)

    # 兜底回答
    graph.add_node("llm_direct_out_node", llm_direct_out_node)

    # 小红书发布链路
    graph.add_node("topic_confirm_node", topic_confirm_node)
    graph.add_node("platform_select_node", platform_select_node)
    graph.add_node("text_generate_node", text_generate_node)
    graph.add_node("content_revise_node", content_revise_node)
    graph.add_node("image_generator_node", image_generator_node)
    graph.add_node("check_text_image_node", check_text_image_node)
    graph.add_node("xiaohongshu_auto_publish_node", xiaohongshu_auto_publish_node)
    graph.add_node("generate_markdown_node", generate_markdown_node)

    # ==================== 构建边 ====================

    # START → 全局意图路由
    graph.add_edge(START, "intent_route_node")

    # ---------- 条件边1：全局意图路由 ----------
    def global_intent_router(state: AgentState) -> str:
        """路由到三个主分支：发布 / 医保 / 闲聊"""
        if state.get("is_xiaohongshu_publish_intent"):
            return "topic_confirm_node"
        elif state.get("is_insurance_intent"):
            return "entity_and_intent_node"
        else:
            return "llm_direct_out_node"

    graph.add_conditional_edges(
        "intent_route_node",
        global_intent_router,
        path_map={
            "topic_confirm_node": "topic_confirm_node",
            "entity_and_intent_node": "entity_and_intent_node",
            "llm_direct_out_node": "llm_direct_out_node"
        }
    )

    # ---------- 闲聊兜底分支 ----------
    graph.add_edge("llm_direct_out_node", END)

    # ---------- 条件边2：细意图路由 ----------
    def sub_intent_router(state: AgentState) -> str:
        """根据细意图分发到不同处理链路"""
        sub_intent = state.get("sub_intent", "graph_query")
        router_map = {
            "graph_query": "cypher_generate_node",
            "reimburse_calc": "reimburse_calc_tool",
            "catalog_check": "catalog_check_tool",
            "benefit_compare": "benefit_compare_tool",
            "process_guide": "faiss_retrieve_node"
        }
        return router_map.get(sub_intent, "cypher_generate_node")

    graph.add_conditional_edges(
        "entity_and_intent_node",
        sub_intent_router,
        path_map={
            "cypher_generate_node": "cypher_generate_node",
            "reimburse_calc_tool": "reimburse_calc_tool",
            "catalog_check_tool": "catalog_check_tool",
            "benefit_compare_tool": "benefit_compare_tool",
            "faiss_retrieve_node": "faiss_retrieve_node"
        }
    )

    # ---------- Cypher 查询子链路 ----------
    # cypher_generate → check → 条件分支
    # 注意：cypher_generate_node 内部已包含FAISS匹配，直接生成Cypher
    # 这里简化：cypher_generate 直接到 neo4j_execute，由执行结果判断是否需要降级

    # 图谱查询类：cypher_generate → neo4j_execute → graph_result_sort → result_fusion
    graph.add_edge("cypher_generate_node", "neo4j_execute_node")

    # 条件边3：Neo4j查询结果是否有有效数据
    def graph_result_router(state: AgentState) -> str:
        """判断Cypher查询是否有有效结果"""
        cypher_results = state.get("cypher_results", [])
        has_valid_result = False
        for item in cypher_results:
            result = item.get("result", [])
            error = item.get("error")
            if result and not error:
                has_valid_result = True
                break
        if has_valid_result:
            return "graph_result_sort_node"
        else:
            return "faiss_retrieve_node"

    graph.add_conditional_edges(
        "neo4j_execute_node",
        graph_result_router,
        path_map={
            "graph_result_sort_node": "graph_result_sort_node",
            "faiss_retrieve_node": "faiss_retrieve_node"
        }
    )

    # 有结果 → 整理 → 融合
    graph.add_edge("graph_result_sort_node", "result_fusion_node")

    # 无结果 → FAISS降级 → 整理 → 融合
    graph.add_edge("faiss_retrieve_node", "faiss_result_sort_node")
    graph.add_edge("faiss_result_sort_node", "result_fusion_node")

    # 工具类直接汇入融合节点
    graph.add_edge("reimburse_calc_tool", "result_fusion_node")
    graph.add_edge("catalog_check_tool", "result_fusion_node")
    graph.add_edge("benefit_compare_tool", "result_fusion_node")

    # 办事流程类 → faiss_retrieve → faiss_result_sort → result_fusion
    # (已在上面连接)

    # 融合 → 回答 → 反馈 → END
    graph.add_edge("result_fusion_node", "answer_generate_node")
    graph.add_edge("answer_generate_node", "feedback_collect_node")
    graph.add_edge("feedback_collect_node", END)

    # ---------- 小红书发布链路 ----------
    graph.add_edge("topic_confirm_node", "platform_select_node")
    graph.add_edge("platform_select_node", "text_generate_node")

    # 条件边4：文案合规校验
    def content_valid_router(state: AgentState) -> str:
        """判断文案是否校验通过"""
        if state.get("is_can_publish_xiaohongshu"):
            return "image_generator_node"
        else:
            revise_times = state.get("content_revise_times", 0)
            if revise_times < 2:
                return "content_revise_node"
            else:
                return "generate_markdown_node"

    graph.add_conditional_edges(
        "check_text_image_node",
        content_valid_router,
        path_map={
            "image_generator_node": "image_generator_node",
            "content_revise_node": "content_revise_node",
            "generate_markdown_node": "generate_markdown_node"
        }
    )

    # 文案修改 → 回到文案生成（重新校验）
    graph.add_edge("content_revise_node", "text_generate_node")

    # 文案生成 → 校验
    graph.add_edge("text_generate_node", "check_text_image_node")

    # 校验通过 → 生成配图 → 自动发布
    graph.add_edge("image_generator_node", "xiaohongshu_auto_publish_node")

    # 条件边5：发布结果
    def publish_result_router(state: AgentState) -> str:
        """判断发布是否成功"""
        tip = state.get("xiaohongshu_tip", "")
        if "成功" in tip:
            return "generate_markdown_node"
        else:
            return "generate_markdown_node"  # 无论成功失败都归档

    graph.add_conditional_edges(
        "xiaohongshu_auto_publish_node",
        publish_result_router,
        path_map={
            "generate_markdown_node": "generate_markdown_node"
        }
    )

    # 归档 → END
    graph.add_edge("generate_markdown_node", END)

    # ==================== 编译 ====================
    memory = InMemorySaver()
    app = graph.compile(memory)
    return app


# 构建并输出流程图
graph = build_graph()
output_pic_graph(graph, get_file_path("__004__langgraph_more_nodes/graph.jpg"))


# ==================== 调用入口 ====================
async def insurance_response(input: str, thread_id: str):
    """单轮对话调用入口"""
    config = RunnableConfig(configurable={"thread_id": thread_id})
    result = await graph.ainvoke({"input": input}, config=config)
    return result.get("output", "")


async def insurance_response_stream(input: str, thread_id: str):
    """流式输出：逐token返回LLM生成的内容，实现真正的流式响应"""
    config = RunnableConfig(configurable={"thread_id": thread_id})
    # 直接调用LLM生成最终回答的节点（闲聊兜底 + 医保回答生成）
    answer_nodes = {"llm_direct_out_node", "answer_generate_node"}
    final_output = ""

    # 使用 stream_mode="messages" 捕获LLM的token流
    async for msg, metadata in graph.astream({"input": input}, config=config, stream_mode="messages"):
        node_name = metadata.get("langgraph_node", "")
        if node_name in answer_nodes:
            content = msg.content if hasattr(msg, "content") else ""
            if content:
                final_output += content
                yield content

    # 如果流式没有输出（如走了小红书发布等非LLM直接输出路径），
    # 从最终状态中获取output作为兜底
    if not final_output:
        state = await graph.aget_state(config)
        if state and state.values:
            output = state.values.get("output", "")
            if output:
                yield output


if __name__ == '__main__':
    import asyncio

    # 测试1：医保问答
    print("=" * 60)
    print("测试1：医保问答")
    print("=" * 60)
    result1 = asyncio.run(insurance_response("高血压门诊报销比例是多少？", thread_id="test_001"))
    print(f"回答：{result1}")

    # 测试2：多轮对话
    print("\n" + "=" * 60)
    print("测试2：多轮对话")
    print("=" * 60)
    # result2 = asyncio.run(insurance_response("还有哪些慢特病可以报销", thread_id="test_001"))
    result2 = asyncio.run(insurance_response("还有哪些慢特病可以报销", thread_id="test_001"))
    print(f"回答：{result2}")

    # 测试3：闲聊兜底
    print("\n" + "=" * 60)
    print("测试3：闲聊兜底")
    print("=" * 60)
    result3 = asyncio.run(insurance_response("今天天气怎么样？", thread_id="test_002"))
    print(f"回答：{result3}")
