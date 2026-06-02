"""
百度搜索测试用例。

测试场景：
1. 打开百度
2. 搜索"我是帅哥"
3. 点击第一个搜索结果
4. 验证页面成功打开
"""

import pytest

from auto.pages import BaiduSearchPage
from auto.utils import logger, take_screenshot


class TestBaiduSearch:
    """百度搜索测试类。"""

    @pytest.mark.ui
    @pytest.mark.smoke
    def test_search_and_click_first(self, page):
        """
        测试：搜索并点击第一个结果。

        步骤：
        1. 打开百度首页
        2. 输入搜索词 "我是帅哥"
        3. 点击搜索按钮
        4. 点击第一个搜索结果
        5. 验证新页面打开成功

        预期结果：
        - 成功打开第一个搜索结果对应的页面
        """
        # 创建百度搜索页面对象
        logger.info("初始化百度搜索页面对象")
        baidu_page = BaiduSearchPage(page)

        # 1. 打开百度首页
        logger.info("步骤 1: 打开百度首页")
        baidu_page.open_baidu()
        assert page.url == "https://www.baidu.com/", f"预期 URL 为百度首页，实际: {page.url}"
        logger.info("✅ 百度首页打开成功")

        # 截图
        take_screenshot(page, "01_baidu_homepage")

        # 2. 搜索 "我是帅哥"
        logger.info("步骤 2: 搜索关键词 '我是帅哥'")
        keyword = "我是帅哥"
        baidu_page.search(keyword)
        logger.info(f"✅ 搜索完成，当前 URL: {page.url}")

        # 截图
        take_screenshot(page, "02_search_results")

        # 3. 获取第一个搜索结果的 URL
        logger.info("步骤 3: 获取第一个搜索结果的 URL")
        first_result_url = baidu_page.get_first_result_url()
        logger.info(f"第一个搜索结果 URL: {first_result_url}")
        assert first_result_url, "未能获取第一个搜索结果的 URL"
        logger.info("✅ 成功获取第一个搜索结果 URL")

        # 4. 点击第一个搜索结果
        logger.info("步骤 4: 点击第一个搜索结果")
        baidu_page.click_first_result()
        logger.info(f"✅ 第一个搜索结果已点击，新 URL: {page.url}")

        # 截图
        take_screenshot(page, "03_search_result_page")

        # 5. 验证页面成功打开
        logger.info("步骤 5: 验证页面成功打开")
        current_url = page.url
        assert current_url != "https://www.baidu.com/", f"页面未成功跳转，URL 仍为: {current_url}"
        logger.info(f"✅ 页面成功打开，URL: {current_url}")

        # 最终截图
        take_screenshot(page, "04_final_result")

        logger.info("✅ 测试用例通过：成功搜索并点击第一个结果")
