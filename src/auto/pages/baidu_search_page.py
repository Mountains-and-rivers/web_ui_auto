"""
百度搜索页面对象模块。

定义百度搜索页面的元素定位和操作方法。
"""

from playwright.sync_api import Page

from ..core.base_page import BasePage
from ..utils.coordinates import get_center_coordinates
from ..utils.logger import logger


class BaiduSearchPage(BasePage):
    """
    百度搜索页面对象。

    Attributes:
        page: Playwright Page 对象
        timeout: 默认超时时间
    """

    # 页面元素定位器
    SEARCH_INPUT = 'input[id="kw"]'  # 搜索输入框
    SEARCH_BUTTON = 'button[id="su"]'  # 搜索按钮
    SEARCH_RESULTS = 'div.result'  # 搜索结果列表
    FIRST_RESULT_LINK = 'div.result h3 a'  # 第一个搜索结果链接

    def __init__(self, page: Page, timeout: int = 30000):
        """
        初始化百度搜索页面。

        Args:
            page: Playwright Page 对象
            timeout: 默认超时时间（毫秒）
        """
        super().__init__(page, timeout)

    def open_baidu(self) -> None:
        """打开百度首页。"""
        try:
            logger.info("打开百度首页")
            self.goto("https://www.baidu.com")
            logger.info("百度首页打开成功")
        except Exception as e:
            logger.error(f"打开百度首页失败: {e}")
            raise

    def search(self, keyword: str) -> None:
        """
        在百度进行搜索。

        Args:
            keyword: 搜索关键词
        """
        try:
            logger.info(f"搜索关键词: {keyword}")
            
            center_x, center_y = get_center_coordinates(self.page, 238)
            self.input_text_by_coordinates(center_x, center_y, keyword)
            logger.info(f"已输入搜索词: {keyword}")

            # 点击搜索按钮
            self.click(self.SEARCH_BUTTON)
            logger.info("已点击搜索按钮")

            # 等待搜索结果加载
            self.wait_for_navigation()
            logger.info("搜索结果已加载")
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            raise

    def get_first_result_url(self) -> str:
        """
        获取第一个搜索结果的 URL。

        Returns:
            第一个搜索结果的链接 URL

        Raises:
            ElementNotFoundError: 搜索结果不存在
        """
        try:
            logger.info("获取第一个搜索结果的 URL")
            # 查找第一个搜索结果
            first_result = self.page.locator(self.FIRST_RESULT_LINK).first
            first_result.wait_for(timeout=self.timeout, state="visible")

            # 获取链接 href
            url = first_result.get_attribute("href")
            logger.info(f"第一个搜索结果 URL: {url}")
            return url or ""
        except Exception as e:
            logger.error(f"获取搜索结果 URL 失败: {e}")
            raise

    def click_first_result(self) -> None:
        """
        点击第一个搜索结果。

        Raises:
            ElementNotFoundError: 搜索结果不存在
        """
        try:
            logger.info("点击第一个搜索结果")
            # 查找并点击第一个搜索结果
            first_result = self.page.locator(self.FIRST_RESULT_LINK).first
            first_result.wait_for(timeout=self.timeout, state="visible")
            first_result.click(timeout=self.timeout)
            logger.info("第一个搜索结果已点击")

            # 等待新页面加载
            self.wait_for_navigation()
            logger.info("结果页面加载完成")
        except Exception as e:
            logger.error(f"点击搜索结果失败: {e}")
            raise


__all__ = ["BaiduSearchPage"]
