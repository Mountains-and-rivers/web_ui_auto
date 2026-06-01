"""
调试脚本：获取电脑分辨率和百度输入框位置信息。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
from auto.encoding_fix import fix_encoding
fix_encoding()

from playwright.sync_api import sync_playwright
from src.auto.utils.logger import logger


def get_resolution_info():
    """获取分辨率和输入框位置信息。"""
    logger.info("=" * 60)
    logger.info("开始获取分辨率和位置信息")
    logger.info("=" * 60)
    
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=False)
    
    # 获取屏幕尺寸
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080}
    )
    page = context.new_page()
    
    # 打开百度
    logger.info("打开百度首页...")
    page.goto("https://www.baidu.com", wait_until="networkidle")
    
    # 获取浏览器信息
    viewport = page.viewport_size
    logger.info(f"\n浏览器视口分辨率: {viewport['width']} x {viewport['height']}")
    
    # 获取输入框信息
    search_input = page.locator('input[id="kw"]')
    
    try:
        # 尝试使用 is_visible 检查
        logger.info("等待输入框加载...")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        
        # 尝试获取输入框位置，即使它是隐藏的
        bounding_box = search_input.bounding_box()
        
        if bounding_box:
            logger.info(f"\n搜索输入框信息:")
            logger.info(f"  X 坐标: {bounding_box['x']}")
            logger.info(f"  Y 坐标: {bounding_box['y']}")
            logger.info(f"  宽度: {bounding_box['width']}")
            logger.info(f"  高度: {bounding_box['height']}")
            
            # 计算输入框中心坐标
            center_x = int(bounding_box['x'] + bounding_box['width'] / 2)
            center_y = int(bounding_box['y'] + bounding_box['height'] / 2)
            
            logger.info(f"\n输入框中心坐标: ({center_x}, {center_y})")
            logger.info(f"推荐使用坐标: ({center_x}, {center_y})")
            
            # 保存信息到文件
            info = f"""浏览器视口: {viewport['width']} x {viewport['height']}
输入框位置: X={bounding_box['x']}, Y={bounding_box['y']}
输入框大小: {bounding_box['width']} x {bounding_box['height']}
推荐坐标: ({center_x}, {center_y})
"""
            
            with open("debug_coordinates.txt", "w", encoding="utf-8") as f:
                f.write(info)
            
            logger.info("\n信息已保存到 debug_coordinates.txt")
        else:
            logger.error("无法获取输入框位置")
    except Exception as e:
        logger.error(f"错误: {e}")
    finally:
        page.close()
        context.close()
        browser.close()
        playwright.stop()
    
    logger.info("=" * 60)
    logger.info("信息获取完成，请查看控制台输出或 debug_coordinates.txt 文件")
    logger.info("=" * 60)


if __name__ == "__main__":
    get_resolution_info()
