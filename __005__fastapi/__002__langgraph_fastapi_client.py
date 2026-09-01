import json

import requests

BACKEND_URL = "http://127.0.0.1:8001/process"
BACKEND_STREAM_URL = "http://127.0.0.1:8001/process_stream"


def query_insurance_fastapi(input: str, user_id: str = "default") -> str:
    """同步请求 /process 接口，返回完整回答"""
    payload = {"input": input, "user_id": user_id}

    res = requests.post(BACKEND_URL, json=payload, timeout=120)
    if res.status_code != 200:
        raise RuntimeError(f"服务端异常，状态码：{res.status_code}，响应：{res.text[:200]}")
    if not res.text:
        raise RuntimeError("服务端返回空响应，请确认 FastAPI 服务已正常启动")
    try:
        json_dict = res.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError(f"响应不是 JSON：{res.text[:200]}")
    return json_dict.get("output", "后端没有结果，请稍后重试。")


def query_insurance_fastapi_stream(input: str, user_id: str = "default"):
    """流式请求 /process_stream 接口，逐块返回生成器（配合 st.write_stream 使用）"""
    payload = {"input": input, "user_id": user_id}
    res = requests.post(BACKEND_STREAM_URL, json=payload, timeout=120, stream=True)
    res.encoding = "utf-8"
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


if __name__ == '__main__':
    # # 同步调用测试
    # print(query_insurance_fastapi("高血压门诊报销比例是多少？", user_id="user_001"))

    # 流式调用测试
    for piece in query_insurance_fastapi_stream("职工基本医疗保险的支付方式是什么", user_id="user_001"):
        print(piece, end="", flush=True)

