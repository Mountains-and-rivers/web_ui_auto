#!/bin/bash
# 全量测试脚本

# 设置测试环境
export TEST_ENV=dev

echo "========== 开始全量测试 =========="
echo "测试环境: $TEST_ENV"
echo ""

# 执行所有测试用例
pytest tests/ -v \
    --tb=short \
    --alluredir=reports/allure-results

echo ""
echo "========== 全量测试完成 =========="
echo ""
echo "生成 Allure 报告..."
allure serve reports/allure-results
