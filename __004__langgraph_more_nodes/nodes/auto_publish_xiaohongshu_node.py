from playwright.async_api import async_playwright
import os
import asyncio

from __004__langgraph_more_nodes.agent_state import AgentState
from common.path_utils import get_file_path


class XiaohongshuUploader:
    COOKIE_PATH = get_file_path("cookie/xiaohongshu_cookie_state.json")
    PUBLISH_URL = (
        "https://creator.xiaohongshu.com/publish/publish?from=homepage&target=image&source=official"
    )

    def __init__(self, image_path_list, title: str = "", content: str = ""):
        self.image_path_list = image_path_list
        self.title = title
        self.content = content
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def launch(self):
        print("开始启动")
        self.playwright = await async_playwright().start()
        print("启动完成")
        self.browser = await self.playwright.chromium.launch(headless=False)

        if os.path.exists(self.COOKIE_PATH):
            print("[√] 加载已保存的登录状态...")
            self.context = await self.browser.new_context(
                storage_state=self.COOKIE_PATH,
                permissions=["geolocation"],
                geolocation={"latitude": 31.2304, "longitude": 121.4737},
            )
        else:
            print("[!] 未检测到登录状态，创建新上下文...")
            self.context = await self.browser.new_context(
                permissions=["geolocation"],
                geolocation={"latitude": 31.2304, "longitude": 121.4737},
            )

        self.page = await self.context.new_page()
        await self.page.goto(self.PUBLISH_URL)

        if not os.path.exists(self.COOKIE_PATH):
            input("请手动登录后按回车继续...")
            os.makedirs(os.path.dirname(self.COOKIE_PATH), exist_ok=True)
            await self.context.storage_state(path=self.COOKIE_PATH)
            print("[√] 登录状态已保存")
        await self.wait_seconds(1)

    async def switch_to_image_post(self):
        print("🔀 正在切换到【上传图文】Tab...")

        try:
            await self.page.wait_for_selector(".creator-tab .title", timeout=10000)

            tabs = await self.page.query_selector_all(".creator-tab .title")
            target_tab = None

            for tab in tabs:
                text = (await tab.inner_text()).strip()
                if "上传图文" in text:
                    box = await tab.bounding_box()
                    if box and box["x"] > 0 and box["y"] > 0:
                        target_tab = tab
                        break

            if target_tab:
                await target_tab.click(force=True)
                print("[√] 已成功切换到【上传图文】Tab")
            else:
                print("[x] 未找到可点击的【上传图文】Tab")

        except Exception as e:
            print(f"[X] 切换失败: {e}")

    async def upload_images(self, images=None):
        print("📤 正在上传图片...")

        try:
            if images is None:
                images = self.image_path_list

            await self.page.wait_for_selector('input.upload-input[type="file"]', state="attached", timeout=10000)
            file_input = await self.page.query_selector('input.upload-input[type="file"]')

            if file_input:
                await file_input.set_input_files(images)
                print(f"[√] 已上传 {len(images)} 张图片")
            else:
                print("[x] 未找到图片上传输入框")

        except Exception as e:
            print(f"[X] 图片上传失败: {e}")

    async def fill_title_and_content(self):
        print("📝 正在填写标题和正文...")

        try:
            title_input = await self.page.wait_for_selector(
                'input.d-text[placeholder*="填写标题"]', timeout=10000
            )
            await title_input.fill(self.title)
            print(f"[√] 标题已填写：{self.title}")
        except:
            print("[x] 未找到标题输入框")

        try:
            editor = await self.page.wait_for_selector(
                '.tiptap[contenteditable="true"]', timeout=10000
            )
            await editor.click()
            await editor.type(self.content)
            print(f"[√] 正文已填写：{self.content}")
        except:
            print("[x] 未找到正文编辑器")

    async def submit_post(self):
        await self.wait_seconds(3)
        print("🚀 正在尝试点击发布按钮...")

        # 策略1：标准 button:has-text 选择器
        try:
            publish_button = await self.page.wait_for_selector(
                'button:has-text("发布")', timeout=5000
            )
            if publish_button:
                await publish_button.click()
                print("[√] 策略1：button:has-text 发布按钮已点击")
                return
        except Exception as e:
            print(f"[!] 策略1失败: {e}")

        # 策略2：XPath 查找文本包含"发布"的元素（支持嵌套子元素）
        try:
            publish_btn = await self.page.wait_for_selector(
                'xpath=//*[contains(normalize-space(.), "发布") and not(contains(normalize-space(.), "暂存"))]',
                timeout=5000
            )
            if publish_btn:
                await publish_btn.click(force=True)
                print("[√] 策略2：XPath 包含文本发布按钮已点击")
                return
        except Exception as e:
            print(f"[!] 策略2失败: {e}")

        # 策略3：遍历所有元素，找文本恰好为"发布"的
        try:
            elements = await self.page.query_selector_all('*')
            for el in elements:
                tag = await el.evaluate('e => e.tagName')
                text = (await el.inner_text()).strip()
                if text == "发布" and tag in ('BUTTON', 'DIV', 'SPAN', 'A'):
                    await el.click(force=True)
                    print(f"[√] 策略3：遍历找到<{tag}>文本=“发布”并点击")
                    return
        except Exception as e:
            print(f"[!] 策略3失败: {e}")

        # 策略4：通过"暂存离开"按钮定位，点击其右侧兄弟元素
        try:
            save_btn = await self.page.query_selector('text=暂存离开')
            if save_btn:
                box = await save_btn.bounding_box()
                if box:
                    # 发布按钮在暂存离开右侧，约 +150px
                    btn_x = box["x"] + box["width"] + 30
                    btn_y = box["y"] + box["height"] / 2
                    await self.page.mouse.click(btn_x, btn_y)
                    print(f"[√] 策略4：暂存离开右侧坐标点击 ({btn_x:.0f}, {btn_y:.0f})")
                    return
        except Exception as e:
            print(f"[!] 策略4失败: {e}")

        # 策略5：页面底部居中区域暴力点击
        try:
            viewport = self.page.viewport_size
            btn_x = viewport["width"] * 0.55
            btn_y = viewport["height"] - 45
            await self.page.mouse.click(btn_x, btn_y)
            print(f"[√] 策略5：底部居中坐标点击 ({btn_x:.0f}, {btn_y:.0f})")
        except Exception as e:
            print(f"[X] 所有策略均失败: {e}")

    # # 发布按钮穿透较为困难, 如果尝试多种方案后无法点击发布按钮, 可通过暴力方法基于坐标点击
    # async def submit_post(self):
    #     await self.wait_seconds(3)
    #     print("🚀 正在尝试点击发布按钮...")
    #
    #     try:
    #         # 方案1：基于坐标点击（按钮在底部居中，约 120px 宽）
    #         # 先获取发布按钮容器的位置
    #         publish_container = await self.page.wait_for_selector(
    #             'xhs-publish-btn', timeout=10000
    #         )
    #         box = await publish_container.bounding_box()
    #
    #         if box:
    #             # 按钮在容器内居中偏右
    #             # 根据截图：容器高度 90px，按钮宽 120px 高 40px，居中排列
    #             # 两个按钮：【暂存离开】在左，【发布】在右，gap 24px
    #             # 发布按钮中心约在整个容器宽度的 65% 位置，垂直居中
    #             btn_x = box["x"] + box["width"] * 0.65
    #             btn_y = box["y"] + box["height"] / 2
    #
    #             await self.page.mouse.click(btn_x, btn_y)
    #             print(f"[√] 已通过坐标点击发布按钮 ({btn_x:.0f}, {btn_y:.0f})")
    #             return
    #
    #     except Exception as e:
    #         print(f"坐标点击失败: {e}")

    async def close(self):
        await self.wait_seconds(4)
        await self.browser.close()
        await self.playwright.stop()

    async def wait_seconds(self, seconds):
        print(f"⏳ 等待 {seconds} 秒...")
        await self.page.wait_for_timeout(seconds * 1000)


async def auto_publish_xiaohongshu(images, title, content):
    xhs = XiaohongshuUploader(images, title, content)
    await xhs.launch()
    await xhs.switch_to_image_post()
    await xhs.upload_images()
    await xhs.fill_title_and_content()
    await xhs.submit_post()
    await xhs.close()


async def xiaohongshu_auto_publish_node(state: AgentState):
    """根据用户输入生成医保科普类的小红书文案（包括标题、内容、策略）"""
    print("开始发布小红书")
    title = state["xiaohongshu_post_title"]
    content = state["xiaohongshu_post_content"]
    images = state["xiaohongshu_image_path_list"]

    await auto_publish_xiaohongshu(images, title, content)

    # await auto_publish_xiaohongshu(images, title, content)
    state["xiaohongshu_tip"] = "小红书发布成功！"
    print("完成发布小红书")
    return state


# FastAPI 或脚本运行入口
if __name__ == "__main__":
    #    asyncio.run(
    #        auto_publish_xiaohongshu(
    #            images=[get_file_path("picture/20260723183950吃荔枝有什.png")],
    #            title="中医养生",
    #            content="中医养生hahha",
    #        )
    #    )
    asyncio.run(xiaohongshu_auto_publish_node(
        state=AgentState(xiaohongshu_image_path_list=[get_file_path("picture/20260814115107医保报销怎.png")],
                         xiaohongshu_post_title="医保报销指南",
                         xiaohongshu_post_content="门诊、住院、慢特病报销流程详解")))