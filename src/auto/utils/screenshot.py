"""
截图管理模块 - 页面截图和 Allure 报告集成。

提供屏幕截图功能，支持：
- 保存截图文件
- Allure 报告附件集成
- 失败自动截图
"""

from pathlib import Path
from typing import Optional

from playwright.sync_api import Page

from auto.utils.logger import logger


def take_screenshot(page: Page, name: str = "screenshot") -> str:
    """
    获取页面截图。

    Args:
        page: Playwright Page 对象
        name: 截图名称（不含扩展名）

    Returns:
        截图文件路径，失败返回 None

    Raises:
        Exception: 截图失败
    """
    try:
        # 构建截图路径
        screenshot_dir = Path(__file__).parent.parent.parent.parent / "artifacts" / "screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        screenshot_path = screenshot_dir / f"{name}.png"

        # 检查页面是否可用
        if not page.is_closed():
            # 获取截图
            page.screenshot(path=str(screenshot_path))
            logger.info(f"截图已保存: {screenshot_path}")

            # 尝试附加到 Allure 报告
            try:
                import allure

                with open(screenshot_path, "rb") as f:
                    allure.attach.file(
                        source=screenshot_path,
                        name=f"{name}.png",
                        attachment_type=allure.attachment_type.PNG,
                    )
                logger.debug(f"截图已附加到 Allure 报告: {name}")
            except ImportError:
                logger.debug("Allure 未安装，跳过报告附件")

            return str(screenshot_path)
        else:
            logger.warning(f"页面已关闭，无法截图: {name}")
            return None
    except Exception as e:
        logger.error(f"截图失败: {name}, 错误: {e}")
        return None


def take_element_screenshot(page: Page, locator: str, name: str = "element") -> str:
    """
    获取元素截图。

    Args:
        page: Playwright Page 对象
        locator: 元素定位器
        name: 截图名称（不含扩展名）

    Returns:
        截图文件路径

    Raises:
        Exception: 截图失败
    """
    try:
        screenshot_dir = Path(__file__).parent.parent.parent.parent / "artifacts" / "screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        screenshot_path = screenshot_dir / f"{name}.png"
        element = page.locator(locator)
        element.screenshot(path=str(screenshot_path))

        logger.info(f"元素截图已保存: {screenshot_path}")
        return str(screenshot_path)
    except Exception as e:
        logger.error(f"元素截图失败: {name}, 错误: {e}")
        raise


__all__ = ["take_screenshot", "take_element_screenshot"]
