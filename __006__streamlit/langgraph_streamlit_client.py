# -*- coding: utf-8 -*-
"""
医保政策智能问答系统（基政易答）- Streamlit 前端（HTTP 客户端版）
================================================================
与 langgraph_streamlit.py 的区别：
本文件通过 HTTP 请求调用 __005__fastapi 的后端服务（支持 SSE 流式输出），
前端进程不加载 langgraph/Neo4j/FAISS 等重依赖，启动快、职责解耦。
运行前提：先启动后端服务  python __005__fastapi/__001__langgraph_fastapi.py
运行方式：streamlit run __006__streamlit/langgraph_streamlit_client.py
"""

import json
import uuid

import requests
import streamlit as st

BACKEND_URL = "http://127.0.0.1:8000/process"
BACKEND_STREAM_URL = "http://127.0.0.1:8000/process_stream"


def query_insurance_fastapi(input: str, user_id: str) -> str:
    """同步请求 /process 接口，返回完整回答"""
    payload = {"input": input, "user_id": user_id}
    res = requests.post(BACKEND_URL, json=payload, timeout=120)
    output = res.json().get("output", "后端没有结果，请稍后重试。")
    return output


def query_insurance_fastapi_stream(input: str, user_id: str):
    """流式请求 /process_stream 接口，逐块返回生成器"""
    payload = {"input": input, "user_id": user_id}
    res = requests.post(BACKEND_STREAM_URL, json=payload, timeout=120, stream=True)
    res.encoding = 'utf-8'
    for line in res.iter_lines(decode_unicode=True):
        if line and line.startswith("data: "):
            data_str = line[6:]
            try:
                data = json.loads(data_str)
                if data.get("done"):
                    break
                content = data.get("content", "")
                if content:
                    yield content
            except json.JSONDecodeError:
                continue


CUSTOM_CSS = """
<style>
/* ===== 全局字体与背景（政务蓝白） ===== */
html, body, [class*="css"] {
    font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #f0f5fa 0%, #e8f1f8 50%, #f2f7fb 100%);
}

/* ===== 顶部标题区域 ===== */
.main-header {
    background: linear-gradient(135deg, #1a4f8b 0%, #2c6cb0 40%, #4a90d9 100%);
    padding: 28px 36px;
    border-radius: 16px;
    box-shadow: 0 6px 20px rgba(26, 79, 139, 0.25);
    margin-bottom: 24px;
    text-align: center;
}

.main-header h1 {
    color: #ffffff;
    font-size: 28px;
    font-weight: 700;
    margin: 0;
    letter-spacing: 3px;
}

.main-header p {
    color: #d4e4f4;
    font-size: 14px;
    margin: 8px 0 0 0;
    letter-spacing: 1px;
}

/* ===== 欢迎卡片 ===== */
.welcome-card {
    background: rgba(255, 255, 255, 0.75);
    border: 1px solid #c5dcf0;
    border-radius: 14px;
    padding: 32px 28px;
    text-align: center;
    margin: 40px auto;
    max-width: 560px;
    box-shadow: 0 4px 12px rgba(26, 79, 139, 0.08);
}

.welcome-card .icon {
    font-size: 52px;
    margin-bottom: 12px;
}

.welcome-card h2 {
    color: #1a4f8b;
    font-size: 22px;
    margin: 0 0 10px 0;
    font-weight: 600;
}

.welcome-card p {
    color: #5a7fa6;
    font-size: 15px;
    line-height: 1.8;
    margin: 0;
}

.welcome-card .suggestion-box {
    margin-top: 20px;
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 10px;
}

.welcome-card .suggestion {
    background: #e8f1f8;
    border: 1px solid #b0cde8;
    border-radius: 20px;
    padding: 8px 18px;
    color: #2c6cb0;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s;
}

.welcome-card .suggestion:hover {
    background: #d0e4f4;
    box-shadow: 0 2px 8px rgba(44, 108, 176, 0.2);
}

/* ===== 侧边栏 ===== */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a4f8b 0%, #143b68 100%);
}

section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #a8ccf0;
}

section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stText {
    color: #d4e4f4;
}

section[data-testid="stSidebar"] hr {
    border-color: rgba(168, 204, 240, 0.3);
}

/* ===== 聊天消息气泡 ===== */
[data-testid="stChatMessage"] {
    padding: 12px 0;
    margin-bottom: 8px;
}

[data-testid="stChatMessageAvatarUser"] {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
}

[data-testid="stChatMessageAvatarAssistant"] {
    box-shadow: 0 2px 8px rgba(26, 79, 139, 0.2);
}

/* ===== 聊天输入框 ===== */
[data-testid="stChatInput"] {
    box-shadow: 0 -2px 12px rgba(26, 79, 139, 0.08);
    border-radius: 12px 12px 0 0;
}

[data-testid="stChatInputTextArea"] {
    border-radius: 10px !important;
    border: 2px solid #c5dcf0 !important;
    font-size: 15px !important;
}

/* ===== 加载动画 ===== */
.loading-dots {
    display: inline-block;
}
.loading-dots span {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #2c6cb0;
    margin: 0 3px;
    animation: bounce 1.4s infinite ease-in-out both;
}
.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
    0%, 80%, 100% { transform: scale(0); }
    40% { transform: scale(1.0); }
}

/* ===== 滚动条 ===== */
::-webkit-scrollbar {
    width: 8px;
}
::-webkit-scrollbar-track {
    background: transparent;
}
::-webkit-scrollbar-thumb {
    background: #a8ccf0;
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: #7fb0e0;
}

/* ===== 底部信息 ===== */
.footer {
    text-align: center;
    color: #d4e4f4;
    font-size: 12px;
    padding: 16px 0;
    margin-top: 20px;
}
</style>
"""


def render_welcome_card():
    st.markdown("""
    <div class="welcome-card">
        <div class="icon">🏥</div>
        <h2>欢迎使用医保政策智能问答</h2>
        <p>本系统融合医保知识图谱与大语言模型，<br>
        可为您解答报销比例、医保目录、办理流程等政策问题。</p>
        <div class="suggestion-box">
            <span class="suggestion">💊 高血压门诊报销比例？</span>
            <span class="suggestion">🏥 住院起付线是多少？</span>
            <span class="suggestion">📋 慢特病如何认定？</span>
            <span class="suggestion">🧾 职工和居民医保的区别？</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_header():
    st.markdown("""
    <div class="main-header">
        <h1>🏥 基政易答</h1>
        <p>基于知识图谱与大模型的医保政策智能问答平台</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    with st.sidebar:
        st.markdown("### 🏥 系统信息")
        st.markdown("---")
        st.markdown("**后端地址**")
        st.code(BACKEND_URL, language="text")
        st.markdown(f"**对话轮数**: {len(st.session_state.get('messages', [])) // 2}")
        st.markdown("---")

        st.markdown("### 📋 功能说明")
        st.markdown("""
        - 💊 **报销政策**：门诊/住院报销比例、起付线、封顶线  
        - 📋 **医保目录**：药品、诊疗项目目录查询  
        - 🏥 **办理流程**：慢特病认定、异地就医备案  
        - 🧾 **待遇对比**：职工医保与居民医保待遇对比  
        """)

        st.markdown("---")

        if st.button("🆕 开启新对话", use_container_width=True):
            st.session_state.user_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.rerun()

        if st.button("🗑️ 清空对话", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.markdown("---")
        st.markdown("""
        <div class="footer">
            Powered by LangGraph + Neo4j<br>
            ⚠️ 内容仅供参考，以参保地医保经办机构官方发布为准
        </div>
        """, unsafe_allow_html=True)


def render_loading():
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;padding:8px 0;">
        <span style="color:#2c6cb0;font-size:14px;">🏥 正在为您查询医保政策</span>
        <div class="loading-dots">
            <span></span><span></span><span></span>
        </div>
    </div>
    """, unsafe_allow_html=True)


st.set_page_config(page_title="基政易答 - 医保政策智能问答系统", page_icon="🏥", layout="centered")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

render_sidebar()
render_header()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

if len(st.session_state.messages) == 0:
    render_welcome_card()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "🏥"):
        if msg["role"] == "user":
            st.write(msg["content"])
        else:
            st.markdown(msg["content"], unsafe_allow_html=True)

if prompt := st.chat_input("请输入您的医保问题，如「高血压门诊报销比例是多少？」"):
    with st.chat_message("user", avatar="🧑‍💻"):
        st.write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant", avatar="🏥"):
        try:
            response = st.write_stream(query_insurance_fastapi_stream(prompt, st.session_state.user_id))
        except requests.exceptions.ConnectionError:
            response = "❌ 无法连接后端服务，请先启动 FastAPI 服务：`python __005__fastapi/__001__langgraph_fastapi.py`"
            st.error(response)
        except Exception as e:
            response = f"❌ 请求失败：{str(e)}"
            st.error(response)
        if not response:
            response = "抱歉，本次未能生成回答，请稍后重试。"
    st.session_state.messages.append({"role": "assistant", "content": response})
