from __004__langgraph_more_nodes.agent_state import AgentState


def platform_select_node(state: AgentState) -> dict:
    """
    多平台选择节点。
    确定发布平台（默认小红书），为后续文案风格适配提供依据。
    """
    print("开始平台选择")
    # 默认选择小红书
    platform = "xiaohongshu"

    print(f"完成平台选择: {platform}")
    return {
        "publish_platform": platform
    }


if __name__ == '__main__':
    state = AgentState(input="我想在小红书发一篇关于医保报销流程的笔记")
    result = platform_select_node(state)
    print(result)
