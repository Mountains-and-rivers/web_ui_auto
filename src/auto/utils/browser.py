"""
浏览器工具模块。

封装 Playwright 浏览器启动、上下文创建和页面最大化逻辑，避免重复代码。
"""
from pathlib import Path
from typing import Any, Optional, Tuple

import tkinter as tk
from playwright.sync_api import Browser, BrowserContext, sync_playwright

from auto.utils.logger import logger


def get_screen_resolution() -> Tuple[int, int]:
    """获取系统屏幕分辨率。"""
    root = tk.Tk()
    root.withdraw()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy()
    logger.info(f"系统屏幕分辨率: {screen_width} x {screen_height}")
    return screen_width, screen_height


def _load_chromium_env() -> dict:
    """
    加载 .chromium_env 配置文件。
    
    从项目根目录向上查找配置文件，返回解析后的配置字典。
    仅在手动安装 Chromium 时使用。
    
    Returns:
        配置字典，如 {"CHROMIUM_EXECUTABLE": "..."}
    """
    config = {}
    
    # 查找项目根目录（向上找到包含 setup.py 或 .chromium_env 的目录）
    current = Path(__file__).parent
    for _ in range(5):
        env_file = current / ".chromium_env"
        if env_file.exists():
            for line in env_file.read_text(encoding='utf-8').splitlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
            break
        current = current.parent
    
    return config


def launch_browser(settings: Any) -> tuple[Any, Browser]:
    """启动 Playwright 浏览器并返回 playwright 与 browser 对象。"""
    playwright = sync_playwright().start()
    browser_type = settings.get("browser.type", "chromium")
    headless = settings.get("browser.headless", False)

    # 构建启动参数
    launch_options: dict[str, Any] = {"headless": headless}
    
    # 加载自定义 Chromium 路径配置
    env_config = _load_chromium_env()
    if env_config.get("USE_CUSTOM_CHROMIUM") == "true":
        executable = env_config.get("CHROMIUM_EXECUTABLE")
        if executable and Path(executable).exists():
            launch_options["executable_path"] = executable
            logger.info(f"使用自定义 Chromium: {executable}")

    logger.info(f"浏览器类型: {browser_type}, headless: {headless}")

    if browser_type == "chromium":
        browser = playwright.chromium.launch(**launch_options)
    elif browser_type == "firefox":
        browser = playwright.firefox.launch(**launch_options)
    else:
        browser = playwright.webkit.launch(**launch_options)

    screen_width, screen_height = get_screen_resolution()
    browser.screen_width = screen_width
    browser.screen_height = screen_height

    return playwright, browser


def create_context(browser: Browser, settings: Any) -> BrowserContext:
    """创建浏览器上下文并应用视口、录屏配置。"""
    record_video_dir = None
    if settings.get("video.enabled", True):
        # 使用相对路径，基于当前工作目录
        video_path = settings.get("video.path", "artifacts/videos/")
        video_dir = Path(video_path)
        video_dir.mkdir(parents=True, exist_ok=True)
        record_video_dir = str(video_dir)
        logger.info(f"录屏目录: {record_video_dir}")

    screen_width = getattr(browser, "screen_width", 1920)
    screen_height = getattr(browser, "screen_height", 1080)
    logger.info(f"浏览器分辨率: {screen_width} x {screen_height}")

    return browser.new_context(
        record_video_dir=record_video_dir,
        viewport={"width": screen_width, "height": screen_height},
    )


def maximize_page(page: Any) -> None:
    """最大化页面窗口到当前屏幕大小。"""
    try:
        page.evaluate("window.moveTo(0, 0); window.resizeTo(screen.width, screen.height);")
        logger.info("已最大化浏览器窗口")
    except Exception as e:
        logger.debug(f"JavaScript 最大化失败: {e}")
    finally:
        page.wait_for_timeout(200)
