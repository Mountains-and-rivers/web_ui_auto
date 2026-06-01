"""
页面对象基类模块 - POM 设计模式实现。

BasePage 提供了页面对象的基础功能，包括：
- 元素定位和交互
- 等待机制
- 截图和录屏
- 异常处理和恢复
"""

from typing import Optional, Tuple

from playwright.async_api import Page
from playwright.sync_api import Page as SyncPage
from playwright.sync_api import expect

from ..utils.logger import logger
from ..utils.screenshot import take_screenshot
from .exceptions import ElementNotFoundError, TimeoutError


class BasePage:
    """
    页面对象基类 - 所有页面对象的父类。

    通过 POM 设计模式，将页面元素和操作方法封装在页面对象中，
    提高代码的可维护性和可读性。

    Attributes:
        page: Playwright Page 对象（同步 API）
        timeout: 元素查找默认超时时间（毫秒）
    """

    def __init__(self, page: SyncPage, timeout: int = 30000):
        """
        初始化页面对象。

        Args:
            page: Playwright Page 对象
            timeout: 默认超时时间，单位毫秒，默认 30 秒
        """
        self.page = page
        self.timeout = timeout
        logger.info(f"初始化页面对象: {self.__class__.__name__}")

    def goto(self, url: str) -> None:
        """
        导航到指定 URL。

        Args:
            url: 目标 URL

        Raises:
            TimeoutError: 页面加载超时
        """
        try:
            logger.info(f"导航到 URL: {url}")
            self.page.goto(url, wait_until="networkidle", timeout=self.timeout)
            logger.info(f"成功导航到: {url}")
        except Exception as e:
            logger.error(f"导航失败: {url}, 错误: {e}")
            take_screenshot(self.page, "navigation_failed")
            raise TimeoutError(f"页面加载失败: {url}") from e

    def find_element(self, locator: str, timeout: Optional[int] = None) -> object:
        """
        查找单个元素。

        Args:
            locator: 定位器表达式
            timeout: 查找超时时间（毫秒），为 None 则使用页面对象的默认超时

        Returns:
            Locator 对象

        Raises:
            ElementNotFoundError: 元素未找到
        """
        timeout = timeout or self.timeout
        try:
            logger.debug(f"查找元素: {locator}, 超时: {timeout}ms")
            locator_obj = self.page.locator(locator)
            locator_obj.wait_for(timeout=timeout, state="visible")
            logger.debug(f"元素查找成功: {locator}")
            return locator_obj
        except Exception as e:
            logger.error(f"元素查找失败: {locator}, 错误: {e}")
            take_screenshot(self.page, "element_not_found")
            raise ElementNotFoundError(f"未找到元素: {locator}") from e

    def click(self, locator: str, timeout: Optional[int] = None) -> None:
        """
        点击元素。

        Args:
            locator: 定位器表达式
            timeout: 查找超时时间（毫秒）
        """
        try:
            logger.info(f"点击元素: {locator}")
            element = self.find_element(locator, timeout)
            element.click(timeout=self.timeout)
            logger.info(f"点击成功: {locator}")
        except Exception as e:
            logger.error(f"点击失败: {locator}, 错误: {e}")
            take_screenshot(self.page, "click_failed")
            raise

    def input_text(self, locator: str, text: str, timeout: Optional[int] = None) -> None:
        """
        在元素中输入文本。

        Args:
            locator: 定位器表达式
            text: 要输入的文本
            timeout: 查找超时时间（毫秒）
        """
        try:
            logger.info(f"在元素中输入文本: {locator}, 文本: {text}")
            element = self.find_element(locator, timeout)
            # 先点击元素获得焦点
            element.click(timeout=self.timeout)
            # 等待一下确保焦点已获得
            self.page.wait_for_timeout(100)
            # 清空已有内容
            element.clear(timeout=self.timeout)
            # 使用 type 模拟真实输入，而不是 fill
            element.type(text, delay=50)
            logger.info(f"输入文本成功: {locator}")
        except Exception as e:
            logger.error(f"输入文本失败: {locator}, 错误: {e}")
            take_screenshot(self.page, "input_text_failed")
            raise

    def get_text(self, locator: str, timeout: Optional[int] = None) -> str:
        """
        获取元素文本内容。

        Args:
            locator: 定位器表达式
            timeout: 查找超时时间（毫秒）

        Returns:
            元素文本内容
        """
        try:
            logger.debug(f"获取元素文本: {locator}")
            element = self.find_element(locator, timeout)
            text = element.text_content(timeout=self.timeout)
            logger.debug(f"成功获取文本: {locator}, 内容: {text}")
            return text or ""
        except Exception as e:
            logger.error(f"获取文本失败: {locator}, 错误: {e}")
            raise

    def input_text_by_coordinates(self, x: int, y: int, text: str) -> None:
        """
        通过坐标点击并输入文本。

        Args:
            x: X 坐标
            y: Y 坐标
            text: 要输入的文本
        """
        try:
            logger.info(f"通过坐标输入文本: ({x}, {y}), 文本: {text}")
            # 点击指定坐标
            self.page.mouse.click(x, y)
            logger.info(f"已点击坐标: ({x}, {y})")
            
            # 等待焦点获得
            self.page.wait_for_timeout(100)
            
            # 清空已有内容
            self.page.keyboard.press("Control+A")
            self.page.wait_for_timeout(50)
            
            # 输入文本
            self.page.keyboard.type(text, delay=50)
            logger.info(f"通过坐标输入文本成功: {text}")
        except Exception as e:
            logger.error(f"通过坐标输入文本失败: {e}")
            take_screenshot(self.page, "input_by_coordinates_failed")
            raise

    def is_visible(self, locator: str, timeout: int = 5000) -> bool:
        """
        检查元素是否可见。

        Args:
            locator: 定位器表达式
            timeout: 查找超时时间（毫秒），默认 5 秒

        Returns:
            元素是否可见
        """
        try:
            logger.debug(f"检查元素可见性: {locator}")
            element = self.page.locator(locator)
            element.wait_for(timeout=timeout, state="visible")
            logger.debug(f"元素可见: {locator}")
            return True
        except Exception:
            logger.debug(f"元素不可见: {locator}")
            return False

    def wait_for_navigation(self, timeout: Optional[int] = None) -> None:
        """
        等待页面导航完成。

        Args:
            timeout: 等待超时时间（毫秒）
        """
        timeout = timeout or self.timeout
        try:
            logger.info(f"等待页面导航, 超时: {timeout}ms")
            self.page.wait_for_load_state("networkidle", timeout=timeout)
            logger.info("页面导航完成")
        except Exception as e:
            logger.error(f"等待导航超时: {e}")
            raise TimeoutError("页面导航超时") from e

    def take_screenshot(self, name: str = "screenshot") -> None:
        """
        获取页面截图。

        Args:
            name: 截图文件名（无扩展名）
        """
        try:
            logger.info(f"获取截图: {name}")
            take_screenshot(self.page, name)
            logger.info(f"截图保存成功: {name}")
        except Exception as e:
            logger.error(f"截图失败: {e}")

    def get_page_title(self) -> str:
        """
        获取页面标题。

        Returns:
            页面标题
        """
        title = self.page.title()
        logger.debug(f"页面标题: {title}")
        return title

    def get_page_url(self) -> str:
        """
        获取当前页面 URL。

        Returns:
            当前页面 URL
        """
        url = self.page.url
        logger.debug(f"当前 URL: {url}")
        return url

    def switch_to_frame(self, locator: str) -> "BasePage":
        """
        切换到 iframe。

        Args:
            locator: iframe 定位器

        Returns:
            新的 BasePage 实例，其 page 指向 iframe
        """
        try:
            logger.info(f"切换到 iframe: {locator}")
            frame = self.page.locator(locator).frame
            logger.info("切换成功")
            return BasePage(frame, self.timeout)
        except Exception as e:
            logger.error(f"切换 iframe 失败: {e}")
            raise

    def wait_for_element(self, locator: str, timeout: Optional[int] = None) -> None:
        """
        等待元素出现。

        Args:
            locator: 定位器表达式
            timeout: 等待超时时间（毫秒）
        """
        timeout = timeout or self.timeout
        try:
            logger.info(f"等待元素: {locator}, 超时: {timeout}ms")
            self.page.locator(locator).wait_for(timeout=timeout, state="visible")
            logger.info(f"元素已出现: {locator}")
        except Exception as e:
            logger.error(f"等待元素失败: {locator}, 错误: {e}")
            raise TimeoutError(f"元素等待超时: {locator}") from e

    def refresh_page(self) -> None:
        """刷新页面。"""
        try:
            logger.info("刷新页面")
            self.page.reload(wait_until="networkidle", timeout=self.timeout)
            logger.info("页面刷新成功")
        except Exception as e:
            logger.error(f"页面刷新失败: {e}")
            raise


__all__ = ["BasePage"]
