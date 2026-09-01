from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from common.config import Config

conf = Config()

# ============ 配置llm区域 ============
# 指向 vLLM 部署的微调模型（OpenAI 兼容接口）
# base_url: vLLM 服务地址，替换为你自己的部署地址
# model: 微调后的模型路径/名称（基于医保问答语料微调）
my_llm = ChatOpenAI(
    api_key="EMPTY",
    base_url="https://b2a74d6548da4abd807999fe438af271--8000.ap-shanghai2.cloudstudio.club/v1",
    model="export/qwen2.5-merged_0727/"
)

if __name__ == '__main__':
    # ============ 场景一：医保政策文本知识图谱抽取（微调主用途） ============
    # 构造对话消息：从医保政策文本中抽取知识图谱结构（实体与关系）
    messages = [
        SystemMessage(content="请从以下医保政策文本中抽取知识图谱结构，包括实体（疾病、药品、诊疗项目、参保类型、政策文件、报销规则）与关系。"),
        HumanMessage(
            content="【政策名称】高血压门诊慢特病报销政策\n"
                    "适用参保类型：职工基本医疗保险、城乡居民基本医疗保险\n"
                    "适用病种：高血压（ICD-10编码：I10）\n"
                    "报销规则：经门诊慢特病认定后，政策范围内费用报销比例70%，"
                    "起付线500元，年度封顶线4000元。\n"
                    "办理渠道：参保地医保经办机构或定点医院医保窗口，"
                    "需提供诊断证明、病历资料、身份证及社保卡。")
    ]

    # ============ 场景二：医保政策问答（可选测试） ============
    # messages = [
    #     SystemMessage(content="你是严谨专业的医保政策问答助手，仅基于已知政策信息回答，不确定的内容请明确告知用户咨询参保地医保经办机构。"),
    #     HumanMessage(content="高血压门诊报销比例是多少？需要什么条件？")
    # ]

    # 调用模型（流式输出）
    result = ""
    for chunk in my_llm.stream(messages):
        result += chunk.content
        print(chunk.content, end="", flush=True)
    print("\n")
    print("*" * 100)
    print(result)