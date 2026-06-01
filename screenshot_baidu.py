"""
截图脚本：打开百度并截图以便识别输入框位置。
自动获取系统分辨率并计算输入框坐标。
"""

import sys
from pathlib import Path
import tkinter as tk

sys.path.insert(0, str(Path(__file__).parent / "src"))
from auto.encoding_fix import fix_encoding
fix_encoding()

from playwright.sync_api import sync_playwright


def screenshot_baidu():
    """打开百度并截图，自动计算坐标。"""
    # 获取系统分辨率
    root = tk.Tk()
    root.withdraw()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy()
    
    print(f"系统屏幕分辨率: {screen_width} x {screen_height}")
    
    print("启动浏览器...")
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=False, args=["--start-maximized"])
    
    context = browser.new_context(viewport={"width": screen_width, "height": screen_height})
    page = context.new_page()
    
    print("按 F11 进入全屏模式...")
    page.keyboard.press("F11")
    page.wait_for_timeout(500)
    
    print("打开百度首页...")
    page.goto("https://www.baidu.com", wait_until="networkidle")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    
    # 截图
    screenshot_path = Path(__file__).parent / "baidu_screenshot.png"
    page.screenshot(path=str(screenshot_path))
    print(f"截图已保存到: {screenshot_path}")
    
    # 获取输入框的bounding box（即使隐藏也可以获取）
    search_input = page.locator('input[id="kw"]')
    bbox = search_input.bounding_box()
    
    if bbox:
        center_x = int(bbox['x'] + bbox['width']/2)
        center_y = int(bbox['y'] + bbox['height']/2)
        
        print(f"\n输入框位置信息:")
        print(f"  X: {bbox['x']}")
        print(f"  Y: {bbox['y']}")
        print(f"  宽: {bbox['width']}")
        print(f"  高: {bbox['height']}")
        print(f"  中心坐标: ({center_x}, {center_y})")
        
        # 保存信息
        info = f"""系统屏幕分辨率: {screen_width} x {screen_height}
浏览器视口: {page.viewport_size['width']} x {page.viewport_size['height']}
输入框位置: X={bbox['x']}, Y={bbox['y']}
输入框大小: {bbox['width']} x {bbox['height']}
推荐坐标: ({center_x}, {center_y})
"""
        
        with open("debug_coordinates.txt", "w", encoding="utf-8") as f:
            f.write(info)
        
        print("\n坐标信息已保存到 debug_coordinates.txt")
    else:
        print("无法获取输入框位置")
    
    # 保持浏览器开启，让用户查看
    print("\n浏览器已打开，可以查看截图。按 Enter 键关闭...")
    input()
    
    page.close()
    context.close()
    browser.close()
    playwright.stop()
    print("完成")


if __name__ == "__main__":
    screenshot_baidu()
