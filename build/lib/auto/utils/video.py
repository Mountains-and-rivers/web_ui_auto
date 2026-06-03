"""
视频录制模块 - Playwright 页面录屏。

提供页面录制功能，支持：
- 录屏文件直接保存为指定文件名（使用 Playwright 原生 video.save_as()）
- 视频路径获取
- 临时文件清理
"""

from pathlib import Path
from typing import Optional, Union
import shutil

from playwright.sync_api import Page

from auto.utils.logger import logger


def save_video_with_name(
    page: Page, 
    video_name: str, 
    video_dir: Optional[Union[str, Path]] = None,
    overwrite: bool = True
) -> Optional[str]:
    """
    使用 Playwright 原生方法保存录屏为指定文件名。
    
    在 context 关闭前调用，通过 page.video.save_as() 直接保存到指定路径。
    
    Args:
        page: Playwright Page 对象
        video_name: 视频文件名（不含扩展名），例如 "smoke"、"login_test"
        video_dir: 视频保存目录，默认为 artifacts/videos
        overwrite: 是否覆盖已存在的文件，默认 True
        
    Returns:
        保存后的视频文件完整路径，失败返回 None
        
    Raises:
        ValueError: 当 video_name 为空或包含非法字符时
        
    Example:
        >>> # 基本用法
        >>> save_video_with_name(page, "smoke")
        
        >>> # 自定义保存目录
        >>> save_video_with_name(page, "my_test", "/custom/path")
        
        >>> # 不覆盖已存在的文件
        >>> save_video_with_name(page, "test_video", overwrite=False)
    """
    try:
        # 验证参数
        if not video_name or not video_name.strip():
            raise ValueError("视频文件名不能为空")
        
        # 清理文件名中的非法字符
        video_name = _sanitize_filename(video_name.strip())
        
        if not video_name:
            raise ValueError("视频文件名包含非法字符")
        
        # 检查是否有录屏
        if not hasattr(page, 'video') or not page.video:
            logger.warning("页面没有录屏，跳过保存")
            return None
        
        # 确定视频目录
        if video_dir is None:
            video_dir_path = Path(__file__).parent.parent.parent.parent / "artifacts" / "videos"
        else:
            video_dir_path = Path(video_dir)
        
        # 确保目录存在
        video_dir_path.mkdir(parents=True, exist_ok=True)
        
        # 构建目标路径
        target_path = video_dir_path / f"{video_name}.webm"
        
        # 如果文件已存在且不允许覆盖，添加序号
        if not overwrite and target_path.exists():
            counter = 1
            while target_path.exists():
                target_path = video_dir_path / f"{video_name}_{counter}.webm"
                counter += 1
            logger.info(f"文件已存在，保存为: {target_path.name}")
        
        # 使用 Playwright 原生方法保存视频
        page.video.save_as(str(target_path))
        logger.info(f"✅ 录屏已保存为: {target_path.name}")
        
        return str(target_path)
    
    except ValueError as e:
        logger.error(f"参数错误: {e}")
        return None
    except Exception as e:
        logger.error(f"保存录屏失败: {e}")
        logger.debug(f"异常详情: {type(e).__name__}: {e}", exc_info=True)
        return None


def _sanitize_filename(filename: str) -> str:
    """
    清理文件名中的非法字符。
    
    Args:
        filename: 原始文件名
        
    Returns:
        清理后的文件名
    """
    # 替换常见的非法字符
    illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    sanitized = filename
    
    for char in illegal_chars:
        sanitized = sanitized.replace(char, '_')
    
    # 去除首尾空格
    sanitized = sanitized.strip()
    
    # 限制长度（Windows 文件名最大 255 字符）
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    
    return sanitized


def get_video_path(page: Page) -> Optional[str]:
    """
    获取页面视频文件路径。
    
    注意：必须在页面或 context 关闭后才能获取到最终路径。

    Args:
        page: Playwright Page 对象

    Returns:
        视频文件路径或 None
    """
    try:
        if not hasattr(page, 'video') or not page.video:
            return None
        
        video_path = page.video.path()
        logger.debug(f"视频文件路径: {video_path}")
        return str(video_path)
    except Exception as e:
        logger.error(f"获取视频路径失败: {e}")
        return None


def delete_video(page: Page) -> bool:
    """
    删除页面的录屏文件。
    
    用于不需要保留录屏的场景，节省磁盘空间。

    Args:
        page: Playwright Page 对象

    Returns:
        是否删除成功
    """
    try:
        if not hasattr(page, 'video') or not page.video:
            logger.warning("页面没有录屏，无需删除")
            return False
        
        page.video.delete()
        logger.info("✅ 录屏文件已删除")
        return True
    except Exception as e:
        logger.error(f"删除录屏文件失败: {e}")
        return False


def cleanup_temp_videos(video_dir: Optional[Union[str, Path]] = None) -> int:
    """
    清理临时录屏文件。
    
    删除指定目录下所有 page@ 开头的临时录屏文件，保留正式的录屏文件（如 smoke.webm）。

    Args:
        video_dir: 录屏目录路径，默认为 artifacts/videos

    Returns:
        清理的文件数量
    """
    try:
        if video_dir is None:
            video_dir = Path(__file__).parent.parent.parent.parent / "artifacts" / "videos"
        else:
            video_dir = Path(video_dir)
        
        if not video_dir.exists():
            logger.warning(f"录屏目录不存在: {video_dir}")
            return 0
        
        # 只删除 page@ 开头的临时文件
        temp_files = list(video_dir.glob("page@*.webm"))
        
        if not temp_files:
            logger.debug("没有临时录屏文件需要清理")
            return 0
        
        deleted_count = 0
        for temp_file in temp_files:
            temp_file.unlink()
            deleted_count += 1
            logger.info(f"️ 已删除临时文件: {temp_file.name}")
        
        if deleted_count > 0:
            # 统计保留的正式文件数量
            formal_files = [f for f in video_dir.glob("*.webm") if not f.name.startswith("page@")]
            logger.info(f"✅ 清理完成: 删除 {deleted_count} 个临时文件，保留 {len(formal_files)} 个正式文件")
        
        return deleted_count
    
    except Exception as e:
        logger.error(f"清理临时录屏文件失败: {e}")
        return 0


def cleanup_temp_dir(video_dir: Optional[Union[str, Path]] = None) -> bool:
    """
    清理临时录屏目录（整个 .temp_videos 目录）。
    
    删除包含所有 Playwright 生成的临时录屏文件的隐藏目录。

    Args:
        video_dir: 录屏目录路径，默认为 artifacts/videos

    Returns:
        是否清理成功
    """
    try:
        if video_dir is None:
            video_dir = Path(__file__).parent.parent.parent.parent / "artifacts" / "videos"
        else:
            video_dir = Path(video_dir)
        
        if not video_dir.exists():
            logger.warning(f"录屏目录不存在: {video_dir}")
            return False
        
        # 临时目录路径
        temp_dir = video_dir / ".temp_videos"
        
        if not temp_dir.exists():
            logger.debug(f"临时目录不存在: {temp_dir}")
            return False
        
        # 统计临时文件数量
        temp_files = list(temp_dir.glob("*.webm"))
        file_count = len(temp_files)
        
        # 删除整个临时目录
        shutil.rmtree(temp_dir)
        
        if file_count > 0:
            logger.info(f"✅ 已清理临时目录 {temp_dir.name}，包含 {file_count} 个临时文件")
        else:
            logger.info(f"✅ 已清理临时目录 {temp_dir.name}")
        
        return True
    
    except Exception as e:
        logger.error(f"清理临时目录失败: {e}")
        return False


__all__ = [
    "save_video_with_name", 
    "get_video_path", 
    "delete_video",
    "cleanup_temp_videos",
    "cleanup_temp_dir"
]
