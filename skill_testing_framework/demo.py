#!/usr/bin/env python3
"""
完整演示：企业级Skill测试框架
展示单元测试、集成测试、端到端测试的完整流程
"""

from example_skills import create_skill_registry_with_examples
from unit_test_framework import SkillUnitTester, TriggerTestSuite
from integration_test_framework import (
    SkillIntegrationTester,
    IntegrationTestCase,
    PerformanceTester
)
from e2e_test_framework import E2ETestRunner, E2ETestCase, WorkflowStep, RegressionDetector
from test_runner import UnifiedTestRunner, ContinuousTestingPipeline


def demo_unit_tests():
    """演示单元测试"""
    print("\n" + "=" * 70)
    print("DEMO 1: UNIT TESTS")
    print("=" * 70)
    print("\n单元测试验证skill的定义、触发条件、参数等基本属性")

    registry = create_skill_registry_with_examples()
    code_review_skill = registry.get("code-review")

    print(f"\n测试Skill: {code_review_skill.metadata.name}")
    print(f"描述: {code_review_skill.metadata.description}")

    tester = SkillUnitTester(code_review_skill)
    results = tester.run_all_tests()
    tester.print_results()

    print("\n💡 单元测试关注点：")
    print("  - Metadata完整性（名称、版本、描述）")
    print("  - 触发条件是否明确")
    print("  - 参数定义是否完整")
    print("  - Examples和Red flags是否存在")


def demo_trigger_tests():
    """演示触发条件测试"""
    print("\n" + "=" * 70)
    print("DEMO 2: TRIGGER CONDITION TESTS")
    print("=" * 70)
    print("\n触发条件测试验证skill在正确的情况下被调用")

    registry = create_skill_registry_with_examples()
    code_review_skill = registry.get("code-review")

    trigger_suite = TriggerTestSuite(code_review_skill)

    test_cases = [
        {
            "input": "Please review code for my function",
            "should_trigger": True
        },
        {
            "input": "Can you code review this?",
            "should_trigger": True
        },
        {
            "input": "Generate some code for me",
            "should_trigger": False
        },
        {
            "input": "Help me debug",
            "should_trigger": False
        }
    ]

    print("\n运行触发条件测试用例：")
    results = trigger_suite.test_trigger_matching(test_cases)

    for idx, result in enumerate(results):
        status = "✅" if result.status.value == "passed" else "❌"
        test_case = test_cases[idx]
        print(f"{status} '{test_case['input'][:40]}...' -> should_trigger={test_case['should_trigger']}")

    print("\n💡 触发条件测试确保：")
    print("  - Skill在正确的上下文中被触发")
    print("  - 避免误触发（false positives）")
    print("  - 关键词匹配准确")


def demo_integration_tests():
    """演示集成测试"""
    print("\n" + "=" * 70)
    print("DEMO 3: INTEGRATION TESTS")
    print("=" * 70)
    print("\n集成测试验证skill的实际执行、参数传递和返回值")

    registry = create_skill_registry_with_examples()

    # 定义集成测试用例
    test_cases = [
        IntegrationTestCase(
            name="test_code_review_success",
            description="Test successful code review",
            skill_name="code-review",
            input_params={
                "code": "def add(a, b):\n    return a + b",
                "language": "python"
            },
            expected_output_type="dict",
            should_succeed=True
        ),
        IntegrationTestCase(
            name="test_code_review_empty_code",
            description="Test code review with empty code",
            skill_name="code-review",
            input_params={
                "code": "",
                "language": "python"
            },
            should_succeed=True  # 应该成功但会有issues
        ),
        IntegrationTestCase(
            name="test_test_generator",
            description="Test test generator skill",
            skill_name="test-generator",
            input_params={
                "function_name": "calculate",
                "function_code": "def calculate(x, y): return x * y",
                "test_framework": "pytest"
            },
            should_succeed=True
        ),
        IntegrationTestCase(
            name="test_invalid_framework",
            description="Test with invalid test framework",
            skill_name="test-generator",
            input_params={
                "function_name": "test_func",
                "function_code": "def test_func(): pass",
                "test_framework": "invalid_framework"
            },
            should_succeed=False  # 应该失败（validation error）
        )
    ]

    tester = SkillIntegrationTester(registry)
    results = tester.run_test_suite(test_cases)
    tester.print_results()

    print("\n💡 集成测试验证：")
    print("  - Skill能够正确执行")
    print("  - 参数验证生效")
    print("  - 返回值符合预期")
    print("  - 错误处理正确")


def demo_performance_tests():
    """演示性能测试"""
    print("\n" + "=" * 70)
    print("DEMO 4: PERFORMANCE BENCHMARKS")
    print("=" * 70)
    print("\n性能基准测试追踪skill的执行速度")

    registry = create_skill_registry_with_examples()
    perf_tester = PerformanceTester(registry)

    print("\n运行性能基准测试（100次迭代）...")
    benchmark = perf_tester.benchmark_skill(
        skill_name="code-review",
        params={
            "code": "def example():\n    return 'hello'",
            "language": "python"
        },
        iterations=100
    )

    print(f"\n📊 性能指标:")
    print(f"  总运行次数: {benchmark['iterations']}")
    print(f"  成功: {benchmark['successful']}")
    print(f"  失败: {benchmark['failed']}")
    print(f"  平均耗时: {benchmark['avg_ms']:.2f}ms")
    print(f"  最小耗时: {benchmark['min_ms']:.2f}ms")
    print(f"  最大耗时: {benchmark['max_ms']:.2f}ms")
    print(f"  P95: {benchmark['p95_ms']:.2f}ms")
    print(f"  P99: {benchmark['p99_ms']:.2f}ms")

    print("\n💡 性能测试用途：")
    print("  - 建立性能baseline")
    print("  - 检测性能退化")
    print("  - 优化热点识别")
    print("  - SLA验证")


def demo_regression_detection():
    """演示回归检测"""
    print("\n" + "=" * 70)
    print("DEMO 5: REGRESSION DETECTION")
    print("=" * 70)
    print("\n回归检测对比当前指标与baseline，自动发现质量下降")

    detector = RegressionDetector()

    # 模拟baseline指标
    baseline = {
        "total_tests": 50,
        "passed": 48,
        "failed": 2,
        "errors": 0,
        "pass_rate": "96.00%",
        "avg_duration_ms": 125.5,
        "timestamp": "2025-01-20T10:00:00"
    }
    detector.save_baseline(baseline)
    print("✅ Baseline已保存")

    # 场景1: 无回归
    print("\n场景1: 质量保持 (无回归)")
    current_good = {
        "total_tests": 50,
        "passed": 48,
        "failed": 2,
        "errors": 0,
        "pass_rate": "96.00%",
        "avg_duration_ms": 120.0,
        "timestamp": "2025-01-24T10:00:00"
    }
    result = detector.detect_regression(current_good)
    print(f"  结果: {result['message']}")

    # 场景2: 有回归
    print("\n场景2: 质量下降 (检测到回归)")
    current_bad = {
        "total_tests": 50,
        "passed": 42,
        "failed": 8,
        "errors": 0,
        "pass_rate": "84.00%",
        "avg_duration_ms": 200.0,
        "timestamp": "2025-01-24T11:00:00"
    }
    result = detector.detect_regression(current_bad)
    if result["has_regression"]:
        print(f"  ⚠️  {result['message']}")
        for reg in result["regressions"]:
            print(f"    - {reg['metric']}: {reg['baseline']} → {reg['current']} ({reg['change']})")

    print("\n💡 回归检测价值：")
    print("  - 自动发现质量下降")
    print("  - 防止性能退化")
    print("  - CI/CD集成")
    print("  - 趋势分析")


def demo_unified_runner():
    """演示统一测试运行器"""
    print("\n" + "=" * 70)
    print("DEMO 6: UNIFIED TEST RUNNER")
    print("=" * 70)
    print("\n统一测试运行器整合所有测试类型，提供一站式测试体验")

    registry = create_skill_registry_with_examples()
    runner = UnifiedTestRunner(registry)

    print("\n运行完整测试套件（单元测试 + 集成测试）...")

    # 准备集成测试用例
    integration_tests = [
        IntegrationTestCase(
            name="quick_integration_test",
            description="Quick integration smoke test",
            skill_name="code-review",
            input_params={"code": "print('hello')", "language": "python"},
            should_succeed=True
        )
    ]

    results = runner.run_all_tests(
        run_unit=True,
        run_integration=True,
        run_e2e=False,  # E2E tests need project setup
        integration_tests=integration_tests,
        detect_regression=True
    )

    # 导出结果
    runner.export_results("demo_test_results.json")

    print("\n💡 统一运行器优势：")
    print("  - 一次运行所有测试")
    print("  - 统一的结果报告")
    print("  - 自动回归检测")
    print("  - 结果持久化")


def demo_ci_cd_integration():
    """演示CI/CD集成"""
    print("\n" + "=" * 70)
    print("DEMO 7: CI/CD INTEGRATION")
    print("=" * 70)
    print("\n持续测试管道支持pre-commit hooks、on-change testing等")

    registry = create_skill_registry_with_examples()
    pipeline = ContinuousTestingPipeline(registry)

    print("\n场景1: Pre-commit Hook")
    print("模拟提交前运行测试...")
    passed = pipeline.run_pre_commit_hook()
    if passed:
        print("✅ Pre-commit tests passed - commit allowed")
    else:
        print("❌ Pre-commit tests failed - commit blocked")

    print("\n场景2: On Skill Change")
    print("模拟skill修改后的自动测试...")
    skill_passed = pipeline.run_on_skill_change("code-review")
    if skill_passed:
        print("✅ Skill change validated")
    else:
        print("❌ Skill change has issues")

    print("\n💡 CI/CD集成场景：")
    print("  - Pre-commit hooks: 阻止有问题的提交")
    print("  - On-change testing: 快速反馈")
    print("  - Nightly tests: 完整的E2E验证")
    print("  - Release gates: 发布前质量检查")


def main():
    """运行所有演示"""
    print("\n" + "=" * 70)
    print("企业级Agent Skill测试框架 - 完整演示")
    print("=" * 70)
    print("\n这个演示将展示：")
    print("  1. 单元测试 - 验证skill定义")
    print("  2. 触发条件测试 - 验证触发逻辑")
    print("  3. 集成测试 - 验证skill执行")
    print("  4. 性能测试 - 建立性能baseline")
    print("  5. 回归检测 - 自动发现质量下降")
    print("  6. 统一测试运行器 - 一站式测试")
    print("  7. CI/CD集成 - 持续测试管道")

    input("\n按Enter继续...")

    demo_unit_tests()
    input("\n按Enter继续下一个演示...")

    demo_trigger_tests()
    input("\n按Enter继续下一个演示...")

    demo_integration_tests()
    input("\n按Enter继续下一个演示...")

    demo_performance_tests()
    input("\n按Enter继续下一个演示...")

    demo_regression_detection()
    input("\n按Enter继续下一个演示...")

    demo_unified_runner()
    input("\n按Enter继续下一个演示...")

    demo_ci_cd_integration()

    print("\n" + "=" * 70)
    print("演示完成！")
    print("=" * 70)
    print("\n主要收获：")
    print("\n1. 三层测试金字塔")
    print("   - 单元测试：快速验证skill定义")
    print("   - 集成测试：验证skill执行和参数")
    print("   - 端到端测试：验证完整工作流")
    print("\n2. 自动化质量保障")
    print("   - 回归检测：自动发现质量下降")
    print("   - 性能基准：追踪执行速度")
    print("   - 持续测试：CI/CD集成")
    print("\n3. 企业级最佳实践")
    print("   - 结构化的skill定义")
    print("   - 可复现的测试环境")
    print("   - 完整的测试覆盖")
    print("   - 自动化的测试管道")
    print("\n查看 README.md 了解更多详情")
    print("=" * 70)


if __name__ == "__main__":
    main()
