from typing import TypedDict, List

# LangGraph 智能体状态定义：医保政策问答 + 小红书科普发布双链路
class AgentState(TypedDict):
    # ========== 基础输入输出 & 会话记忆 ==========
    input: str                     # 用户原始输入
    history_messages: List[dict]   # 对话历史，支持多轮指代消解
    output: str                    # 最终统一输出结果

    # ========== 全局意图识别结果 ==========
    is_xiaohongshu_publish_intent: bool  # 是否有小红书/内容发布意图
    is_insurance_intent: bool            # 是否为医保业务相关问题

    # ========== 小红书发布全链路字段 ==========
    xiaohongshu_post_title: str          # 文案标题
    xiaohongshu_post_content: str        # 文案正文
    xiaohongshu_image_path_list: List[str]  # 配图本地路径列表
    xiaohongshu_tip: str                 # 小贴士/话题标签
    is_can_publish_xiaohongshu: bool     # 素材是否校验通过
    xiaohongshu_markdown_output: str     # 发布记录 markdown 归档

    # ========== 医保问答 - 用户输入实体抽取结果 ==========
    user_input_diseases: List[str]       # 疾病病种
    user_input_medicines: List[str]      # 药品
    user_input_treat_items: List[str]    # 诊疗项目
    user_input_insure_types: List[str]   # 参保类型
    user_input_policy_docs: List[str]    # 政策文件
    user_input_rules: List[str]          # 报销规则

    # ========== 医保问答 - 向量匹配后的标准实体 ==========
    matched_diseases: List[str]
    matched_medicines: List[str]
    matched_treat_items: List[str]
    matched_insure_types: List[str]
    matched_policy_docs: List[str]
    matched_rules: List[str]

    # ========== 医保问答 - Cypher 查询链路 ==========
    cypher_query: List[str]        # 生成的 Cypher 语句集合
    is_all_validate_cypher: bool   # 全部 Cypher 是否语法合法
    cypher_retry_times: int        # Cypher 重试次数，控制循环上限
    cypher_results: List[dict]     # Neo4j 查询结果
    neo4j_answer: str              # 纯图谱结果生成的回答

    # ========== 医保问答 - 向量检索降级链路 ==========
    retrieved_docs: List[dict]     # FAISS 召回的政策文档片段
    answer_sources: List[str]      # 回答溯源信息列表

    # ========== 通用兆底输出 ==========
    direct_out: str                # 非医保问题直接大模型回答

    # ========== 医保问答 - 细意图分类 ==========
    sub_intent: str                # 细意图：graph_query/reimburse_calc/catalog_check/benefit_compare/process_guide

    # ========== 医保问答 - 结果整理中间字段 ==========
    graph_result_text: str         # 图谱查询结果的结构化文本
    faiss_result_text: str         # FAISS检索结果的结构化文本
    fusion_context: str            # 多源融合后的上下文
    tool_result: dict              # 工具输出结果
    tool_type: str                 # 工具类型标识

    # ========== 医保问答 - Cypher校验错误信息 ==========
    cypher_error_info: str         # Cypher校验不通过时的错误信息

    # ========== 小红书发布 - 选题与平台 ==========
    publish_topic: str             # 发布主题
    publish_key_points: List[str]  # 核心知识点
    publish_target_audience: str   # 目标受众
    publish_platform: str          # 发布平台

    # ========== 小红书发布 - 文案修改 ==========
    content_revise_times: int      # 文案修改重试次数
    revise_reason: str             # 文案修改原因

    # ========== 问答记录 ==========
    qa_record: dict                # 本次问答关键信息记录