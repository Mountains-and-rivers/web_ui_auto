"""
pytest 全局 fixture 配置。

定义全局的 fixture，包括：
- 日志记录
- 失败处理
- 配置 browser_context_args 供 pytest-playwright 使用
- 浏览器分辨率和窗口最大化
- 重写 page fixture 支持自定义录屏文件名
"""

# 导入编码修复模块
import auto.encoding_fix  # noqa: F401

import os
import time
import traceback
import tkinter as tk
import pytest
from _pytest.outcomes import Skipped
from pathlib import Path

# 导入核心组件
from auto.utils.logger import logger, set_framework_logger, set_case_logger, clear_case_logger
from auto.utils.screenshot import take_screenshot
from auto.utils.video import save_video_with_name, cleanup_temp_dir
from config.settings import get_settings


def get_screen_resolution() -> tuple:
    """获取系统屏幕分辨率。"""
    root = tk.Tk()
    root.withdraw()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy()
    logger.info(f"系统屏幕分辨率: {screen_width} x {screen_height}")
    return screen_width, screen_height


@pytest.fixture(scope="session")
def settings():
    """
    获取全局配置。

    Scope: session（整个测试会话）
    """
    env = os.getenv("TEST_ENV", "dev")
    logger.info(f"测试环境: {env}")
    return get_settings(env)


@pytest.fixture(scope="session")
def browser_context_args(settings):
    """
    配置 pytest-playwright 的浏览器上下文参数。
    
    在浏览器启动时就设置好视口大小，确保立即最大化。
    将录屏临时文件保存到隐藏目录 .temp_videos 中，避免污染主目录。
    
    Args:
        settings: 全局配置
        
    Returns:
        dict: 浏览器上下文配置
    """
    # 获取屏幕分辨率
    screen_width, screen_height = get_screen_resolution()
    
    # 录屏配置 - 使用隐藏目录存储临时文件
    video_enabled = settings.get("video.enabled", True)
    video_path = settings.get("video.path", "artifacts/videos/")
    
    # 设置 viewport 为屏幕分辨率
    context_args = {
        "viewport": {"width": screen_width, "height": screen_height},
    }
    
    if video_enabled:
        # 创建隐藏目录用于存储 Playwright 生成的临时录屏文件
        # 使用 .temp_videos 作为临时目录名（以 . 开头在大多数系统中是隐藏的）
        video_dir = Path(video_path)
        temp_video_dir = video_dir / ".temp_videos"
        temp_video_dir.mkdir(parents=True, exist_ok=True)
        
        context_args["record_video_dir"] = str(temp_video_dir)
        logger.info(f"启用录屏，临时文件目录: {temp_video_dir}")
    
    logger.info(f"浏览器上下文视口设置为: {screen_width} x {screen_height}")
    
    return context_args


@pytest.fixture(scope="function")
def page(context, request):
    """
    重写 pytest-playwright 的 page fixture。
    
    在 context 关闭前调用 save_video_with_name() 直接保存录屏为指定文件名。
    
    Args:
        context: pytest-playwright 提供的 browser context
        request: pytest request 对象，用于获取测试用例信息
        
    Yields:
        Page: Playwright Page 对象
    """
    page = context.new_page()
    yield page
    
    # 在 context 关闭前保存录屏
    try:
        # 获取所有 marks
        all_marks = list(request.node.iter_markers())
        all_marks_reversed = list(reversed(all_marks))
        
        if len(all_marks_reversed) >= 2:
            # 使用第二个 mark 作为录屏文件名
            video_name = all_marks_reversed[1].name
            logger.info(f"准备保存录屏: {video_name}")
            
            # 调用封装的方法直接保存
            save_video_with_name(page, video_name)
        else:
            logger.debug("测试用例标记不足2个，跳过录屏保存")
    except Exception as e:
        logger.warning(f"保存录屏失败: {e}")
    
    page.close()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    pytest hook - 收集测试报告信息。
    """
    outcome = yield
    report = outcome.get_result()
    return report


def pytest_configure(config):
    """
    pytest hook - 配置阶段。

    Args:
        config: pytest 配置对象
    """
    # 切换到框架日志模式
    set_framework_logger()
    
    logger.info("pytest 配置完成")


def pytest_unconfigure(config):
    """
    pytest hook - 清理阶段。

    Args:
        config: pytest 配置对象
    """
    logger.info("pytest 清理完成")
    
    # 清理临时录屏目录（整个 .temp_videos 目录）
    try:
        # 获取视频目录
        video_path = "artifacts/videos/"
        
        # 清理临时目录
        cleanup_temp_dir(video_path)
    except Exception as e:
        logger.warning(f"清理临时录屏目录失败: {e}")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """
    pytest hook - 执行测试函数并在同一个 hook 中收集标签、执行结果、执行日志。
    """
    # 获取测试文件名（去掉 .py 后缀）
    test_file = item.fspath.basename.replace('.py', '')
    
    # 先设置用例日志
    set_case_logger(test_file)
    
    # 记录测试开始日志
    logger.info(f"========== 开始执行用例: {item.nodeid} ==========")
    
    log_messages = []

    def _sink(message):
        log_messages.append(str(message).rstrip("\n"))

    sink_id = logger.add(_sink, level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}")

    # 清空初始化时的日志，仅收集测试用例执行时的日志
    log_messages.clear()

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
    except Exception as exc:
        failed = True
        excinfo = exc
    finally:
        # 先记录测试结束日志
        logger.info(f"========== 用例执行结束 ==========")
        
        # 先移除 sink，停止收集日志
        logger.remove(sink_id)
        
        # 等待日志写入完成
        time.sleep(0.05)
        
        # 清除用例日志设置
        clear_case_logger()

        tags = [marker.name for marker in item.iter_markers() if marker.name != "parametrize"]
        tags_text = ", ".join(tags) if tags else "无"

        if passed:
            result_text = "✅ PASSED"
        elif skipped:
            result_text = "⚠️ SKIPPED"
        else:
            result_text = " FAILED"

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

        if failed:
            try:
                if "page" in item.fixturenames:
                    page = item.funcargs.get("page")
                    if page:
                        logger.error("测试失败，保存失败截图")
                        take_screenshot(page, f"failure_{item.name}")
            except Exception as e:
                logger.warning(f"失败截图保存失败: {e}")


__all__ = ["settings", "browser_context_args"]
