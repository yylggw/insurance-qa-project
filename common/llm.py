from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from common.config import Config

conf = Config()

# ============ 配置llm区域 ============
my_llm = ChatOpenAI(
    api_key=conf.MODEL_API_KEY,
    base_url=conf.MODEL_BASE_URL,
    model=conf.MODEL_NAME
)

if __name__ == '__main__':
    print("===== LLM 连通性测试开始 =====")
    # 构造简单提问消息
    # 手动构造两轮对话消息列表
    messages = [
        HumanMessage(content="什么是模型的url"),
    ]
    resp = my_llm.invoke(messages)
    print(resp.content)
    print("===== LLM 连通性测试结束 =====")