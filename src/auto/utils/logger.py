"""
日志管理模块 - 统一的日志记录封装。

提供日志记录功能，支持：
- 按天切割日志文件
- 控制台和文件同时输出
- 多级别日志控制
- 框架日志和用例日志分离
"""

import sys
from pathlib import Path
from datetime import datetime

from loguru import logger as _logger

# 日志输出目录 - 使用绝对路径
LOG_DIR = Path(__file__).parent.parent.parent.parent / "logs"
FRAMEWORK_LOG_DIR = LOG_DIR / "framework"
CASES_LOG_DIR = LOG_DIR / "cases"

# 确保日志目录存在（使用绝对路径）
LOG_DIR.mkdir(parents=True, exist_ok=True)
FRAMEWORK_LOG_DIR.mkdir(parents=True, exist_ok=True)
CASES_LOG_DIR.mkdir(parents=True, exist_ok=True)

# 移除默认处理器
_logger.remove()

# 添加控制台输出（不使用彩色，避免编码问题）
_console_handler_id = _logger.add(
    sys.stdout,
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    colorize=False,
)

# 添加框架日志文件输出（按天切割）
_framework_handler_id = _logger.add(
    str(FRAMEWORK_LOG_DIR / "{time:YYYY-MM-DD}.log"),
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    rotation="00:00",  # 每天午夜切割
    retention="7 days",  # 保留 7 天日志
    encoding="utf-8",  # 明确指定编码
    enqueue=True,  # 使用队列，线程安全
)

# 当前用例的 handler ID（用于清理）
_current_case_handler_id = None


def set_case_logger(case_name: str):
    """为当前用例设置独立的日志文件。
    
    关键：临时移除 framework 日志 handler，避免日志重复写入
    
    Args:
        case_name: 用例名称
    """
    global _current_case_handler_id
    
    # 如果之前有用例 handler，先移除
    if _current_case_handler_id is not None:
        _logger.remove(_current_case_handler_id)
    
    # 临时移除 framework 日志 handler，避免用例日志写入 framework
    _logger.remove(_framework_handler_id)
    
    # 生成完整的日志文件路径
    today = datetime.now().strftime("%Y-%m-%d")
    log_filename = f"{case_name}_{today}.log"
    log_filepath = CASES_LOG_DIR / log_filename
    
    # 添加用例日志文件 handler
    # 不使用 rotation，避免文件被重命名
    # 不使用 enqueue，确保立即写入
    _current_case_handler_id = _logger.add(
        str(log_filepath),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        encoding="utf-8",
        enqueue=False,  # 不使用队列，立即写入
    )


def clear_case_logger():
    """清除用例日志设置，恢复为框架日志。"""
    global _current_case_handler_id
    
    if _current_case_handler_id is not None:
        _logger.remove(_current_case_handler_id)
        _current_case_handler_id = None
    
    # 重新添加 framework 日志 handler，恢复框架日志记录
    _logger.add(
        str(FRAMEWORK_LOG_DIR / "{time:YYYY-MM-DD}.log"),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="00:00",
        retention="7 days",
        encoding="utf-8",
        enqueue=True,
    )


# 为向后兼容，导出默认 logger
logger = _logger

__all__ = ["logger", "set_case_logger", "clear_case_logger"]
