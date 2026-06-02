"""
pytest 全局 fixture 配置。

定义全局的 fixture，包括：
- 日志记录
- 失败处理
- 配置 browser_context_args 供 pytest-playwright 使用
- 浏览器分辨率和窗口最大化
"""

# 导入编码修复模块
import auto.encoding_fix  # noqa: F401

import os
import traceback
import tkinter as tk
import pytest
from _pytest.outcomes import Skipped
from pathlib import Path

# 导入核心组件
from auto.utils.logger import logger
from auto.utils.screenshot import take_screenshot
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
    
    Args:
        settings: 全局配置
        
    Returns:
        dict: 浏览器上下文配置
    """
    # 获取屏幕分辨率
    screen_width, screen_height = get_screen_resolution()
    
    # 录屏配置
    video_enabled = settings.get("video.enabled", True)
    video_path = settings.get("video.path", "artifacts/videos/")
    
    # 设置 viewport 为屏幕分辨率
    context_args = {
        "viewport": {"width": screen_width, "height": screen_height},
    }
    
    if video_enabled:
        # 创建录屏目录
        video_dir = Path(video_path)
        video_dir.mkdir(parents=True, exist_ok=True)
        context_args["record_video_dir"] = str(video_dir)
        logger.info(f"启用录屏，目录: {video_dir}")
    
    logger.info(f"浏览器上下文视口设置为: {screen_width} x {screen_height}")
    
    return context_args


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    pytest hook - 在测试完成后重命名录屏文件为用例的第二个 mark。
    """
    outcome = yield
    report = outcome.get_result()
    
    # 在 teardown 阶段处理（无论成功还是失败）
    if call.when == "call" or (call.when == "teardown" and hasattr(item, "funcargs")):
        try:
            # 获取所有 marks
            all_marks = list(item.iter_markers())
            print(f"\n{'='*60}")
            print(f"用例: {item.name}")
            print(f"阶段: {call.when}")
            print(f"所有 marks: {[m.name for m in all_marks]}")
            
            # 反转得到从上到下的顺序
            all_marks_reversed = list(reversed(all_marks))
            print(f"反转后 marks: {[m.name for m in all_marks_reversed]}")
            
            if len(all_marks_reversed) >= 2:
                video_name = all_marks_reversed[1].name
                print(f"录屏文件名: {video_name}")
                
                # 获取页面对象并重命名视频
                if "page" in item.funcargs:
                    page = item.funcargs["page"]
                    if page and hasattr(page, 'video') and page.video:
                        try:
                            video_path = page.video.path()
                            print(f"视频路径: {video_path}")
                            
                            if Path(video_path).exists():
                                new_path = Path(video_path).parent / f"{video_name}.webm"
                                Path(video_path).rename(new_path)
                                print(f"✅ 已重命名为: {new_path.name}")
                            else:
                                print(f"⚠️ 视频文件不存在: {video_path}")
                        except Exception as ve:
                            print(f"️ 视频处理错误: {ve}")
            else:
                print(f"️ marks 数量不足: {len(all_marks_reversed)}")
            
            print(f"{'='*60}\n")
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
    
    return report


def pytest_configure(config):
    """
    pytest hook - 配置阶段。

    Args:
        config: pytest 配置对象
    """
    logger.info("pytest 配置完成")


def pytest_unconfigure(config):
    """
    pytest hook - 清理阶段。

    Args:
        config: pytest 配置对象
    """
    logger.info("pytest 清理完成")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """
    pytest hook - 执行测试函数并在同一个 hook 中收集标签、执行结果、执行日志。
    """
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
