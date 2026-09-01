import asyncio
import json
import traceback

import uvicorn
from fastapi import FastAPI, Request            # 导入FastAPI和Request 用来处理HTTP请求
from fastapi.responses import JSONResponse, StreamingResponse  # 导入JSONResponse/StreamingResponse 用来返回JSON/SSE数据
from starlette.staticfiles import StaticFiles   # StaticFiles 用来处理静态文件

from __004__langgraph_more_nodes.langgraph_more_nodes import insurance_response, insurance_response_stream  # 导入医保问答函数（同步+流式）
from common.path_utils import get_file_path     # 在不同设备上获取路径的函数

app = FastAPI()


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """全局兜底：任何未被接口捕获的异常都返回友好JSON，避免500裸奔"""
    traceback.print_exc()
    return JSONResponse(content={"input": "", "output": "系统出错了，请重试！"})

# 将项目根目录下的 picture 文件夹挂载为静态文件服务，通过 URL 路径 /picture 对外提供访问。
app.mount("/picture", StaticFiles(directory=get_file_path("picture")))

@app.post("/process")
async def process(request: Request):
    # 获取传入的 JSON 数据
    try:
        data = await request.json()
        input = data.get("input", "")
        ussr_id = data.get("user_id", "")
        output = await insurance_response(input, ussr_id)
        result = {
            "input": input,
            "output": output if isinstance(output, str) else str(output)
        }
        return JSONResponse(content=result)
    except Exception as e:
        traceback.print_exc()
        result = {
            "input": "",
            "output": "系统出错了，请重试！"
        }
        return JSONResponse(content=result)


@app.post("/process_stream")
async def process_stream(request: Request):
    """流式输出接口，将大模型生成的结果逐token通过SSE推送给客户端"""
    try:
        data = await request.json()
        query = data.get("input", "")
        user_id = data.get("user_id", "")
    except Exception:
        traceback.print_exc()

        async def error_stream():
            yield f"data: {json.dumps({'content': '系统出错了，请重试！', 'done': True}, ensure_ascii=False)}\n\n"

        return StreamingResponse(error_stream(), media_type="text/event-stream")

    async def event_stream():
        try:
            # 使用真正的流式输出，逐token推送LLM生成的内容
            async for chunk in insurance_response_stream(query, user_id):
                # 如果chunk较长（LLM未真正流式时整条返回），拆成小段逐段推送
                chunk_size = 3
                for i in range(0, len(chunk), chunk_size):
                    piece = chunk[i:i + chunk_size]
                    yield f"data: {json.dumps({'content': piece}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.05)
            yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"
        except Exception:
            traceback.print_exc()
            yield f"data: {json.dumps({'content': '系统出错了，请重试！', 'done': True}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)