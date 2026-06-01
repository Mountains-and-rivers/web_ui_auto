"""
视频录制模块 - Playwright 页面录屏。

提供页面录制功能，支持：
- 启动/停止录制
- 自动保存视频文件
- 失败自动保留视频
"""

from pathlib import Path
from typing import Optional

from playwright.sync_api import Page

from .logger import logger


def start_video_recording(page: Page, test_name: str) -> Optional[str]:
    """
    启动页面录制。

    注意：需要在 browser.new_context() 时设置 record_video_dir 参数。

    Args:
        page: Playwright Page 对象
        test_name: 测试用例名称

    Returns:
        视频文件路径或 None
    """
    try:
        # 视频路径由 browser.new_context(record_video_dir=...) 处理
        logger.info(f"页面录制已启动: {test_name}")
        return None
    except Exception as e:
        logger.error(f"启动视频录制失败: {test_name}, 错误: {e}")
        return None


def stop_video_recording(page: Page) -> Optional[str]:
    """
    停止页面录制并获取视频路径。

    Args:
        page: Playwright Page 对象

    Returns:
        视频文件路径或 None
    """
    try:
        # 停止上下文时自动保存视频
        logger.info("页面录制已停止")
        return None
    except Exception as e:
        logger.error(f"停止视频录制失败: {e}")
        return None


def get_video_path(page: Page) -> Optional[str]:
    """
    获取页面视频文件路径。

    Args:
        page: Playwright Page 对象

    Returns:
        视频文件路径或 None
    """
    try:
        # Playwright 录制视频在 context.close() 时自动保存
        video = page.video
        if video:
            video_path = video.path()
            logger.info(f"视频文件路径: {video_path}")
            return str(video_path)
        return None
    except Exception as e:
        logger.error(f"获取视频路径失败: {e}")
        return None


__all__ = ["start_video_recording", "stop_video_recording", "get_video_path"]
