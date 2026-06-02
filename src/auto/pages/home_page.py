"""
首页对象模块（示例）。

定义首页的元素定位和操作方法。
"""

from playwright.sync_api import Page

from auto.core import BasePage
from auto.utils import logger


class HomePage(BasePage):
    """
    首页对象。

    Attributes:
        page: Playwright Page 对象
        timeout: 默认超时时间
    """

    # 页面元素定位器（示例）
    LOGO = 'img[class="logo"]'  # Logo
    NAV_MENU = 'nav.menu'  # 导航菜单
    USER_PROFILE = 'span.user-profile'  # 用户资料

    def __init__(self, page: Page, timeout: int = 30000):
        """
        初始化首页。

        Args:
            page: Playwright Page 对象
            timeout: 默认超时时间（毫秒）
        """
        super().__init__(page, timeout)

    def is_home_page_loaded(self) -> bool:
        """
        检查首页是否加载完成。

        Returns:
            首页是否加载完成
        """
        try:
            logger.info("检查首页是否加载")
            return self.is_visible(self.LOGO, timeout=5000)
        except Exception as e:
            logger.error(f"检查首页失败: {e}")
            return False


__all__ = ["HomePage"]
