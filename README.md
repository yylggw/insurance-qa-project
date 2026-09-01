# 基政易答 — 医保政策智能问答系统

基于知识图谱 + RAG + LangGraph Agent 的医保政策智能问答系统，支持多轮对话、图谱精准检索与向量降级检索。

## 系统架构

```
用户提问 → Streamlit 前端 → FastAPI (SSE流式) → LangGraph Agent 工作流
                                                      ├── 意图路由
                                                      ├── 实体识别
                                                      ├── Cypher 生成 → Neo4j 图谱查询
                                                      ├── FAISS 向量检索（降级兜底）
                                                      ├── 结果融合
                                                      └── 答案生成 → 流式返回
```

## 知识图谱

基于 Neo4j 构建，包含 **7 类实体 + 8 组关系**：

**实体：**
- PolicyDoc（政策文件）、ReimburseRule（报销规则）、Disease（疾病）
- InsureType（参保类型）、Medicine（药品）、TreatItem（诊疗项目）、Agency（经办机构）

**关系：**
- PolicyDoc → STIPULATES → ReimburseRule
- ReimburseRule → RESTRICTS_DISEASE → Disease
- ReimburseRule → APPLIES_TO → InsureType
- Disease → BELONGS_TO_SPECIAL_DISEASE → InsureType
- Disease → CAN_USE → Medicine / TreatItem
- TreatItem → EXECUTED_BY → Agency
- Disease → INCLUDED_IN → PolicyDoc

## 项目结构

```
├── __001__clawler/              # 数据采集（爬虫+数据清洗）
├── __002__extract_information/  # 信息抽取（LLM结构化提取）
├── __003__create_neo4j_database/# 知识图谱构建（Neo4j导入+FAISS嵌入）
├── __004__langgraph_more_nodes/ # LangGraph Agent 工作流（20+节点）
├── __005__fastapi/              # FastAPI 服务端（SSE流式输出）
├── __006__streamlit/            # Streamlit 前端
├── __007__fine_tune/            # 模型微调（LLaMA-Factory + vLLM）
├── common/                      # 公共模块（配置、LLM、Neo4j、嵌入模型）
├── bge-large-zh-v1.5/           # BGE 嵌入模型（需本地下载）
└── requirements.txt             # Python 依赖
```

## 技术栈

| 模块 | 技术 |
|------|------|
| Agent 工作流 | LangGraph |
| 知识图谱 | Neo4j + Cypher |
| 向量检索 | FAISS + BGE-large-zh-v1.5 |
| 大模型 | OpenAI 兼容接口（支持多种后端） |
| 后端服务 | FastAPI + Uvicorn + SSE |
| 前端 | Streamlit |
| 微调 | LLaMA-Factory + LoRA + vLLM |

## 快速开始

### 环境要求
- Python 3.10+
- Neo4j 5.x（本地或远程）
- 大模型 API（OpenAI 兼容接口）

### 安装

```bash
pip install -r requirements.txt
```

### 配置

在项目根目录创建 `.env` 文件：

```env
MODEL_API_KEY=your_api_key
MODEL_BASE_URL=your_model_url
MODEL_NAME=your_model_name
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
EMBEDDING_MODEL_PATH=./bge-large-zh-v1.5
```

### 运行

```bash
# 1. 启动 FastAPI 服务
uvicorn __005__fastapi.__001__langgraph_fastapi:app --reload --port 8000

# 2. 启动 Streamlit 前端
streamlit run __006__streamlit/langgraph_streamlit.py
```

## 工作流程

1. **数据采集**（`__001__clawler/`）：爬取医保政策、药品、疾病、诊疗项目等数据
2. **信息抽取**（`__002__extract_information/`）：LLM 结构化提取实体与关系
3. **图谱构建**（`__003__create_neo4j_database/`）：导入 Neo4j + 生成 FAISS 向量索引
4. **智能问答**（`__004__` ~ `__006__`）：LangGraph Agent 多节点工作流处理用户提问
