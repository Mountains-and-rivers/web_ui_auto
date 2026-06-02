"""
坐标工具模块。

封装页面坐标计算与坐标点击输入逻辑，供页面对象复用。"""
from typing import Tuple

from playwright.sync_api import Page

from .logger import logger
from .screenshot import take_screenshot


def get_center_coordinates(page: Page, y: int, default_width: int = 1920) -> Tuple[int, int]:
    """根据页面视口获取水平中心坐标。"""
    page_size = page.viewport_size
    if page_size and page_size.get("width"):
        center_x = page_size["width"] // 2
        logger.debug(f"页面分辨率: {page_size['width']} x {page_size.get('height', 0)}，计算输入框坐标: ({center_x}, {y})")
    else:
        center_x = default_width // 2
        logger.warning(f"页面大小获取失败，使用默认输入框坐标: ({center_x}, {y})")
    return center_x, y


def click_and_type_by_coordinates(page: Page, x: int, y: int, text: str, delay: int = 50) -> None:
    """通过坐标点击并输入文本。"""
    try:
        logger.info(f"通过坐标输入文本: ({x}, {y}), 文本: {text}")
        page.mouse.click(x, y)
        logger.info(f"已点击坐标: ({x}, {y})")

        page.wait_for_timeout(100)
        page.keyboard.press("Control+A")
        page.wait_for_timeout(50)
        page.keyboard.type(text, delay=delay)
        logger.info(f"通过坐标输入文本成功: {text}")
    except Exception as e:
        logger.error(f"通过坐标输入文本失败: {e}")
        take_screenshot(page, "input_by_coordinates_failed")
        raise
