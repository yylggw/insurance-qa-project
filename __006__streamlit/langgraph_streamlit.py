import asyncio
import uuid
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from langchain_core.runnables import RunnableConfig
from __004__langgraph_more_nodes.langgraph_more_nodes import graph

st.set_page_config(
    page_title="基政易答 - 医保政策智能问答系统",
    page_icon="🏥",
    layout="centered",
)

CUSTOM_CSS = """
<style>
    .stApp {
        background: linear-gradient(135deg, #f0f5fa 0%, #e8f1f8 50%, #f2f7fb 100%);
    }

    .main-header {
        text-align: center;
        padding: 20px 0 10px 0;
        margin-bottom: 10px;
    }
    .main-header h1 {
        color: #1a4f8b;
        font-size: 2.2em;
        font-weight: 700;
        margin-bottom: 4px;
        letter-spacing: 2px;
    }
    .main-header p {
        color: #5a7fa6;
        font-size: 1em;
        margin: 0;
    }
    .main-header .divider {
        width: 60px;
        height: 3px;
        background: linear-gradient(90deg, #4a90d9, #1a4f8b);
        margin: 10px auto 0;
        border-radius: 2px;
    }

    [data-testid="stChatMessage"] {
        background: transparent !important;
        border: none !important;
        padding: 4px 0 !important;
    }

    [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-user"] {
        background: linear-gradient(135deg, #4a90d9, #1a4f8b) !important;
    }
    [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] {
        background: linear-gradient(135deg, #6ba7e0, #2c6cb0) !important;
    }

    .chat-bubble-user {
        background: linear-gradient(135deg, #4a90d9, #1a4f8b);
        color: white;
        padding: 12px 18px;
        border-radius: 18px 18px 4px 18px;
        max-width: 80%;
        margin-left: auto;
        margin-bottom: 6px;
        font-size: 0.95em;
        line-height: 1.6;
        box-shadow: 0 2px 8px rgba(26,79,139,0.15);
    }
    .chat-bubble-assistant {
        background: #ffffff;
        color: #333;
        padding: 14px 18px;
        border-radius: 18px 18px 18px 4px;
        max-width: 85%;
        margin-bottom: 6px;
        font-size: 0.95em;
        line-height: 1.8;
        border: 1px solid #c5dcf0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .chat-bubble-assistant ul, .chat-bubble-assistant ol {
        padding-left: 20px;
        margin: 6px 0;
    }
    .chat-bubble-assistant strong {
        color: #1a4f8b;
    }

    .sidebar-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        border: 1px solid #c5dcf0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    .sidebar-card h3 {
        color: #1a4f8b;
        margin-top: 0;
        font-size: 1em;
    }
    .sidebar-card li {
        color: #555;
        font-size: 0.88em;
        margin-bottom: 4px;
    }

    .thinking-box {
        display: flex;
        align-items: center;
        gap: 10px;
        background: #ffffff;
        border: 1px solid #c5dcf0;
        border-radius: 18px 18px 18px 4px;
        padding: 14px 20px;
        max-width: 260px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .thinking-box .icon {
        font-size: 1.4em;
        animation: pulse 1.5s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.15); }
    }
    .thinking-box .dots span {
        display: inline-block;
        width: 7px;
        height: 7px;
        margin: 0 2px;
        background: #4a90d9;
        border-radius: 50%;
        animation: bounce 1.4s ease-in-out infinite;
    }
    .thinking-box .dots span:nth-child(2) { animation-delay: 0.2s; }
    .thinking-box .dots span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes bounce {
        0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
        40% { transform: scale(1); opacity: 1; }
    }
    .thinking-box .label {
        color: #5a7fa6;
        font-size: 0.88em;
    }

    .stChatInputContainer {
        border-top: 1px solid #c5dcf0 !important;
        background: #f7fafd !important;
    }

    [data-testid="stChatInput"] textarea {
        border-radius: 12px !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #e8f1f8, #f2f7fb) !important;
    }
    [data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #4a90d9, #2c6cb0) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 8px 20px !important;
        font-weight: 500 !important;
        transition: all 0.3s !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(135deg, #2c6cb0, #1a4f8b) !important;
        box-shadow: 0 3px 10px rgba(26,79,139,0.3) !important;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def run_async(coro):
    """在 Streamlit 中安全执行协程（Streamlit 自身已有事件循环，不能直接 asyncio.run）"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


async def get_graph_response(user_input: str, user_id: str) -> str:
    """调用完整 LangGraph 医保智能 Agent 工作流"""
    try:
        config = RunnableConfig(configurable={"thread_id": user_id})
        result = await graph.ainvoke({"input": user_input}, config=config)
        return result.get("output", "") or "抱歉，未能获取到回答。"
    except Exception as e:
        return f"❌ 系统出错了：{str(e)}"


def render_thinking():
    return """
    <div class="thinking-box">
        <span class="icon">🏥</span>
        <span class="dots"><span></span><span></span><span></span></span>
        <span class="label">正在为您查询医保政策...</span>
    </div>
    """


def render_bubble(role: str, content: str):
    """渲染聊天气泡：用户为纯文本，助手支持 Markdown（加粗/列表）"""
    if role == "user":
        escaped = (content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        return f'<div class="chat-bubble-user">{escaped}</div>'
    else:
        return f'<div class="chat-bubble-assistant">{st.markdown(content) if False else content}</div>'


def main():
    st.markdown(
        """
        <div class="main-header">
            <h1>🏥 基政易答</h1>
            <p>医保政策智能问答系统</p>
            <div class="divider"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(
                    f'<div class="chat-bubble-user">{msg["content"]}</div>',
                    unsafe_allow_html=True,
                )
        else:
            with st.chat_message("assistant", avatar="🏥"):
                # 助手回答用 Markdown 渲染，保证加粗/列表正常显示
                bubble_md = f'<div class="chat-bubble-assistant">\n\n{msg["content"]}\n\n</div>'
                st.markdown(bubble_md, unsafe_allow_html=True)

    user_input = st.chat_input("请输入您的医保问题，如：高血压门诊报销比例是多少？")

    if user_input:
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(
                f'<div class="chat-bubble-user">{user_input}</div>',
                unsafe_allow_html=True,
            )
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("assistant", avatar="🏥"):
            thinking_placeholder = st.empty()
            thinking_placeholder.markdown(render_thinking(), unsafe_allow_html=True)
            output = run_async(get_graph_response(user_input, st.session_state.user_id))
            thinking_placeholder.empty()
            if not output:
                output = "抱歉，本次未能生成回答，请稍后重试。"
            bubble_md = f'<div class="chat-bubble-assistant">\n\n{output}\n\n</div>'
            st.markdown(bubble_md, unsafe_allow_html=True)

        st.session_state.messages.append({"role": "assistant", "content": output})

    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-card">
                <h3>📋 你可以问我</h3>
                <ul>
                    <li>门诊/住院报销比例与起付线</li>
                    <li>医保目录内药品与诊疗项目</li>
                    <li>门诊慢特病认定与办理流程</li>
                    <li>职工医保与居民医保待遇对比</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("🆕 开启新对话"):
            st.session_state.messages = []
            st.session_state.user_id = str(uuid.uuid4())
            st.rerun()

        if st.button("🗑️ 清空对话历史"):
            st.session_state.messages = []
            st.rerun()

        st.markdown("---")
        st.caption(f"🏥 基政易答 · 会话ID: {st.session_state.user_id[:8]}...")
        st.caption("⚠️ 免责声明：本系统内容仅供参考，具体政策以参保地医保经办机构官方发布为准。")


if __name__ == "__main__":
    main()