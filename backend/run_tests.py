#!/usr/bin/env python3
"""一键运行单元测试 + 覆盖率分析

对应 PDF：
  - 第 7 页：coverage.py 统计代码覆盖率
  - 第 16 页：运行测试
  - 第 32 页：覆盖率分析

用法：
    python run_tests.py              # 只运行测试
    python run_tests.py --coverage   # 运行测试 + 覆盖率报告
"""

import sys
import os

# 确保后端目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Windows GBK 终端兼容：避免 emoji 编码错误
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

if __name__ == '__main__':
    import unittest

    # --- 收集测试 ---
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='test_*.py')

    # --- 是否启用覆盖率 ---
    use_coverage = '--coverage' in sys.argv
    if use_coverage:
        try:
            import coverage
            cov = coverage.Coverage(source=['app', 'database'])
            cov.start()
            print("[覆盖率分析已启用]\n")
        except ImportError:
            print("[提示] 请先安装 coverage: pip install coverage")
            use_coverage = False

    # --- 运行测试 ---
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # --- 覆盖率报告 ---
    if use_coverage:
        cov.stop()
        cov.save()
        print()
        print("=" * 60)
        print("覆盖率报告")
        print("=" * 60)
        cov.report()
        cov.html_report(directory='coverage_report')
        print(f"\n详细 HTML 报告已生成: coverage_report/index.html")

    # --- 结果汇总 ---
    print()
    print("=" * 60)
    total = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total - failures - errors

    print(f"  总计: {total}  通过: {passed}  失败: {failures}  错误: {errors}")

    if result.wasSuccessful():
        print("[OK] 所有测试通过！")
    else:
        print("[FAIL] 部分测试未通过")
        for name, trace in result.failures:
            print(f"\n  失败: {name}")
            print(f"  {trace.split(chr(10))[-2] if chr(10) in trace else trace}")
        for name, trace in result.errors:
            print(f"\n  错误: {name}")

    sys.exit(0 if result.wasSuccessful() else 1)
