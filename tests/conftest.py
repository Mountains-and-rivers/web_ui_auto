"""
pytest 全局 fixture 配置。

定义全局的 fixture，包括：
- 浏览器和页面对象
- 日志记录
- 截图和录屏
- 失败处理
"""

# 最优先导入编码修复模块，在任何其他导入之前
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from auto.encoding_fix import fix_encoding
fix_encoding()

import os
import traceback
import pytest
from _pytest.outcomes import Skipped
from playwright.sync_api import sync_playwright

# 添加 src 目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from auto.utils.logger import logger
from auto.utils.screenshot import take_screenshot
from config.settings import get_settings


@pytest.fixture(scope="session")
def settings():
    """
    获取全局配置。

    Scope: session（整个测试会话）
    """
    env = os.getenv("TEST_ENV", "dev")
    logger.info(f"测试环境: {env}")
    return get_settings(env)


@pytest.fixture
def browser(settings):
    """
    创建浏览器实例。

    Scope: function（每个测试函数）

    Args:
        settings: 全局配置

    Yields:
        Playwright browser 对象
    """
    logger.info("启动浏览器")
    playwright = sync_playwright().start()

    # 根据配置选择浏览器类型
    browser_type = settings.get("browser.type", "chromium")
    headless = settings.get("browser.headless", False)
    timeout = settings.get("browser.timeout", 30000)

    logger.info(f"浏览器类型: {browser_type}, headless: {headless}")

    if browser_type == "chromium":
        browser = playwright.chromium.launch(headless=headless)
    elif browser_type == "firefox":
        browser = playwright.firefox.launch(headless=headless)
    else:
        browser = playwright.webkit.launch(headless=headless)

    yield browser

    # 清理
    logger.info("关闭浏览器")
    browser.close()
    playwright.stop()


@pytest.fixture
def context(browser, settings):
    """
    创建浏览器上下文。

    Scope: function

    Args:
        browser: 浏览器对象
        settings: 全局配置

    Yields:
        Playwright context 对象
    """
    logger.info("创建浏览器上下文")

    # 录屏配置
    record_video_dir = None
    if settings.get("video.enabled", True):
        video_dir = Path(__file__).parent.parent / settings.get("video.path", "artifacts/videos/")
        video_dir.mkdir(parents=True, exist_ok=True)
        record_video_dir = str(video_dir)
        logger.info(f"录屏目录: {record_video_dir}")

    context = browser.new_context(record_video_dir=record_video_dir)
    yield context

    # 清理
    logger.info("关闭浏览器上下文")
    context.close()


@pytest.fixture
def page(context):
    """
    创建页面对象。

    Scope: function

    Args:
        context: 浏览器上下文

    Yields:
        Playwright page 对象
    """
    logger.info("创建页面对象")
    page = context.new_page()
    yield page

    # 清理
    logger.info("关闭页面对象")
    page.close()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """
    pytest hook - 执行测试函数并在同一个 hook 中收集标签、执行结果、执行日志。
    """
    log_messages = []

    def _sink(message):
        log_messages.append(str(message).rstrip("\n"))

    sink_id = logger.add(_sink, level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}")

    logger.info("========== 测试开始 ==========")
    logger.info(f"用例: {item.nodeid}")
    logger.info(f"测试文件: {item.fspath}")

    passed = False
    skipped = False
    failed = False
    excinfo = None

    try:
        outcome = yield
        outcome.get_result()
        passed = True
    except Skipped as exc:
        skipped = True
        excinfo = exc
        raise
    except Exception as exc:
        failed = True
        excinfo = exc
        raise
    finally:
        logger.remove(sink_id)

    tags = [marker.name for marker in item.iter_markers() if marker.name != "parametrize"]
    tags_text = ", ".join(tags) if tags else "无"

    if passed:
        result_text = "✅ PASSED"
    elif skipped:
        result_text = "⚠️ SKIPPED"
    else:
        result_text = "❌ FAILED"

    summary_lines = [
        f"\n========== 用例执行信息 ==========",
        f"用例: {item.nodeid}",
        f"标签: {tags_text}",
        f"执行结果: {result_text}",
        "执行日志:",
    ]
    summary_lines.extend(log_messages or ["(无日志记录)"])

    if failed and excinfo is not None:
        summary_lines.append("错误原因:")
        if isinstance(excinfo, tuple) and len(excinfo) == 3:
            error_lines = traceback.format_exception(*excinfo)
        elif hasattr(excinfo, "getrepr"):
            error_lines = traceback.format_exception(excinfo.type, excinfo.value, excinfo.tb)
        elif isinstance(excinfo, BaseException):
            error_lines = traceback.format_exception(type(excinfo), excinfo, excinfo.__traceback__)
        else:
            error_lines = [str(excinfo)]
        summary_lines.extend([line.rstrip("\n") for line in error_lines if line.strip()])

    summary_lines.append("========== 用例执行信息结束 ==========")

    for line in summary_lines:
        print(line)
        logger.info(line)

    if failed:
        try:
            if "page" in item.fixturenames:
                page = item.funcargs.get("page")
                if page:
                    logger.error("测试失败，保存失败截图")
                    take_screenshot(page, f"failure_{item.name}")
        except Exception as e:
            logger.warning(f"失败截图保存失败: {e}")



def pytest_configure(config):
    """
    pytest hook - 配置阶段。

    Args:
        config: pytest 配置对象
    """
    logger.info("pytest 配置完成")
    logger.info(f"Python 版本: {sys.version}")


def pytest_unconfigure(config):
    """
    pytest hook - 清理阶段。

    Args:
        config: pytest 配置对象
    """
    logger.info("pytest 清理完成")


__all__ = ["settings", "browser", "context", "page"]
