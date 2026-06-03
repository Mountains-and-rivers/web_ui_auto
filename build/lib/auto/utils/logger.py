"""
日志管理模块 - 统一的日志记录封装。

提供日志记录功能，支持：
- 按天切割日志文件
- 控制台和文件同时输出
- 多级别日志控制
- CLI、框架、用例日志分离
"""

import sys
from pathlib import Path
from datetime import datetime

from loguru import logger as _logger

# 日志输出目录 - 基于当前工作目录（项目根目录）
LOG_DIR = Path.cwd() / "logs"
FRAMEWORK_LOG_DIR = LOG_DIR / "framework"
CASES_LOG_DIR = LOG_DIR / "cases"
CLI_LOG_DIR = LOG_DIR / "web-ui-auto"

# 确保日志目录存在（使用绝对路径）
# 注意：CLI_LOG_DIR 延迟创建，只在 CLI 模式下才创建
for log_dir in [LOG_DIR, FRAMEWORK_LOG_DIR, CASES_LOG_DIR]:
    log_dir.mkdir(parents=True, exist_ok=True)

# 移除默认处理器
_logger.remove()

# 添加控制台输出（启用彩色）
_console_handler_id = _logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True,
)


def _add_file_handler(log_path: str) -> int:
    """添加文件日志 handler。
    
    Args:
        log_path: 日志文件路径（支持 loguru 的时间格式）
        
    Returns:
        handler ID
    """
    return _logger.add(
        log_path,
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="00:00",
        retention="7 days",
        encoding="utf-8",
        enqueue=False,
    )


# 当前激活的 handler ID（用于清理）
_current_handler_id = None

# CLI handler ID（延迟初始化）
_cli_handler_id = None


def init_cli_logger():
    """初始化 CLI 日志模式（仅在 main.py 中调用）。"""
    global _cli_handler_id
    
    print("DEBUG: init_cli_logger() 被调用了!")  # 调试输出
    
    # 确保 CLI 日志目录存在
    CLI_LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"DEBUG: CLI_LOG_DIR = {CLI_LOG_DIR}")  # 调试输出
    
    # 添加 CLI 日志文件输出
    _cli_handler_id = _logger.add(
        str(CLI_LOG_DIR / "{time:YYYY-MM-DD}.log"),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="00:00",
        retention="7 days",
        encoding="utf-8",
        enqueue=False,
    )
    
    print(f"DEBUG: CLI handler 已创建, handler_id={_cli_handler_id}")  # 调试输出


def set_framework_logger():
    """切换到框架日志模式（pytest 启动时调用）。"""
    global _current_handler_id
    
    # 如果 CLI handler 存在，先移除
    if _cli_handler_id is not None:
        _logger.remove(_cli_handler_id)
    
    # 添加 framework handler
    _current_handler_id = _add_file_handler(str(FRAMEWORK_LOG_DIR / "{time:YYYY-MM-DD}.log"))


def set_case_logger(case_name: str):
    """为当前用例设置独立的日志文件。
    
    Args:
        case_name: 用例名称
    """
    global _current_handler_id
    
    if _current_handler_id is not None:
        _logger.remove(_current_handler_id)
    
    today = datetime.now().strftime("%Y-%m-%d")
    log_filename = f"{case_name}_{today}.log"
    log_filepath = CASES_LOG_DIR / log_filename
    
    _current_handler_id = _logger.add(
        str(log_filepath),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        encoding="utf-8",
        enqueue=False,
    )


def clear_case_logger():
    """清除用例日志，恢复为框架日志。"""
    global _current_handler_id
    
    if _current_handler_id is not None:
        _logger.remove(_current_handler_id)
    
    # 恢复 framework handler
    _current_handler_id = _add_file_handler(str(FRAMEWORK_LOG_DIR / "{time:YYYY-MM-DD}.log"))


# 为向后兼容，导出默认 logger
logger = _logger

__all__ = ["logger", "init_cli_logger", "set_framework_logger", "set_case_logger", "clear_case_logger"]
