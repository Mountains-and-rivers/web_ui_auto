#!/bin/bash
# 冒烟测试脚本

# 设置测试环境
export TEST_ENV=dev

echo "========== 开始冒烟测试 =========="
echo "测试环境: $TEST_ENV"
echo ""

# 执行冒烟测试用例
pytest tests/ -v -m smoke \
    --tb=short \
    --alluredir=reports/allure-results

echo ""
echo "========== 冒烟测试完成 =========="
