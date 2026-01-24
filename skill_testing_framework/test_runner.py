"""
统一测试运行器
整合单元测试、集成测试和端到端测试
"""
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from skill_schema import Skill, SkillRegistry
from unit_test_framework import SkillUnitTester, TriggerTestSuite, TestResult, TestStatus
from integration_test_framework import SkillIntegrationTester, IntegrationTestCase, PerformanceTester
from e2e_test_framework import E2ETestRunner, E2ETestCase, RegressionDetector


class UnifiedTestRunner:
    """统一测试运行器"""

    def __init__(self, registry: SkillRegistry):
        self.registry = registry
        self.all_results: List[TestResult] = []
        self.test_start_time = None
        self.test_end_time = None

    def run_all_tests(
        self,
        skills_to_test: Optional[List[str]] = None,
        integration_tests: Optional[List[IntegrationTestCase]] = None,
        e2e_tests: Optional[List[E2ETestCase]] = None,
        run_unit: bool = True,
        run_integration: bool = True,
        run_e2e: bool = True,
        detect_regression: bool = True
    ) -> Dict:
        """运行所有测试"""
        self.test_start_time = time.time()
        self.all_results = []

        print("=" * 70)
        print("ENTERPRISE SKILL TEST SUITE")
        print("=" * 70)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # 确定要测试的skills
        if skills_to_test is None:
            skills = self.registry.list_all()
        else:
            skills = [self.registry.get(name) for name in skills_to_test]
            skills = [s for s in skills if s is not None]

        print(f"Testing {len(skills)} skill(s)")
        print()

        results = {
            "unit_tests": [],
            "integration_tests": [],
            "e2e_tests": [],
            "regression": None
        }

        # 1. 运行单元测试
        if run_unit:
            print("\n" + "=" * 70)
            print("PHASE 1: UNIT TESTS")
            print("=" * 70)

            for skill in skills:
                print(f"\nTesting skill: {skill.metadata.name} v{skill.metadata.version}")
                tester = SkillUnitTester(skill)
                unit_results = tester.run_all_tests()
                tester.print_results()

                self.all_results.extend(unit_results)
                results["unit_tests"].append({
                    "skill": skill.metadata.name,
                    "results": unit_results,
                    "summary": tester.get_summary()
                })

        # 2. 运行集成测试
        if run_integration and integration_tests:
            print("\n" + "=" * 70)
            print("PHASE 2: INTEGRATION TESTS")
            print("=" * 70)

            integration_tester = SkillIntegrationTester(self.registry)
            integration_results = integration_tester.run_test_suite(integration_tests)
            integration_tester.print_results()

            self.all_results.extend(integration_results)
            results["integration_tests"] = {
                "results": integration_results,
                "summary": integration_tester.get_summary()
            }

        # 3. 运行端到端测试
        if run_e2e and e2e_tests:
            print("\n" + "=" * 70)
            print("PHASE 3: END-TO-END TESTS")
            print("=" * 70)

            e2e_runner = E2ETestRunner(self.registry)
            e2e_results = e2e_runner.run_test_suite(e2e_tests)
            e2e_runner.print_results()

            self.all_results.extend(e2e_results)
            results["e2e_tests"] = {
                "results": e2e_results,
                "summary": e2e_runner.get_summary()
            }

        # 4. 回归检测
        if detect_regression:
            print("\n" + "=" * 70)
            print("PHASE 4: REGRESSION DETECTION")
            print("=" * 70)

            regression_detector = RegressionDetector()
            current_metrics = self._compute_overall_metrics(results)

            regression_result = regression_detector.detect_regression(current_metrics)
            results["regression"] = regression_result

            if regression_result["has_regression"]:
                print("\n⚠️  REGRESSION DETECTED!")
                for reg in regression_result["regressions"]:
                    print(f"  - {reg['metric']}: {reg['baseline']} → {reg['current']} ({reg['change']})")
            else:
                print("\n✅ No regressions detected")
                if "improvements" in regression_result and regression_result["improvements"]:
                    print("   Improvements:")
                    for imp in regression_result["improvements"]:
                        print(f"  - {imp['metric']}: {imp['improvement']}")

            # 保存当前指标作为新的baseline
            if regression_result.get("action") == "save_baseline":
                regression_detector.save_baseline(current_metrics)
                print("   Saved current metrics as baseline")

        self.test_end_time = time.time()

        # 5. 打印最终总结
        self._print_final_summary(results)

        return results

    def _compute_overall_metrics(self, results: Dict) -> Dict:
        """计算整体指标"""
        total_tests = len(self.all_results)
        passed = sum(1 for r in self.all_results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.all_results if r.status == TestStatus.FAILED)
        errors = sum(1 for r in self.all_results if r.status == TestStatus.ERROR)

        total_duration = sum(r.duration_ms for r in self.all_results)
        avg_duration = total_duration / total_tests if total_tests > 0 else 0

        return {
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "pass_rate": f"{(passed / total_tests * 100):.2f}%" if total_tests > 0 else "0%",
            "total_duration_ms": total_duration,
            "avg_duration_ms": avg_duration,
            "timestamp": datetime.now().isoformat()
        }

    def _print_final_summary(self, results: Dict):
        """打印最终总结"""
        print("\n" + "=" * 70)
        print("FINAL SUMMARY")
        print("=" * 70)

        metrics = self._compute_overall_metrics(results)

        print(f"\nTotal Tests: {metrics['total_tests']}")
        print(f"  ✅ Passed:  {metrics['passed']}")
        print(f"  ❌ Failed:  {metrics['failed']}")
        print(f"  ⚠️  Errors:  {metrics['errors']}")
        print(f"\nPass Rate: {metrics['pass_rate']}")

        duration_seconds = (self.test_end_time - self.test_start_time)
        print(f"Total Duration: {duration_seconds:.2f}s")
        print(f"Average Test Duration: {metrics['avg_duration_ms']:.2f}ms")

        # 按测试类型分解
        if results["unit_tests"]:
            unit_total = sum(s["summary"]["total"] for s in results["unit_tests"])
            unit_passed = sum(s["summary"]["passed"] for s in results["unit_tests"])
            print(f"\nUnit Tests: {unit_passed}/{unit_total} passed")

        if results["integration_tests"]:
            int_summary = results["integration_tests"]["summary"]
            print(f"Integration Tests: {int_summary['passed']}/{int_summary['total']} passed")

        if results["e2e_tests"]:
            e2e_summary = results["e2e_tests"]["summary"]
            print(f"E2E Tests: {e2e_summary['passed']}/{e2e_summary['total']} passed")

        print("\n" + "=" * 70)

        # 判断整体是否通过
        if metrics["failed"] == 0 and metrics["errors"] == 0:
            print("✅ ALL TESTS PASSED")
        else:
            print("❌ TESTS FAILED")

        print("=" * 70)

    def export_results(self, output_file: str = "test_results.json"):
        """导出测试结果"""
        results_data = {
            "metadata": {
                "start_time": datetime.fromtimestamp(self.test_start_time).isoformat(),
                "end_time": datetime.fromtimestamp(self.test_end_time).isoformat(),
                "duration_seconds": self.test_end_time - self.test_start_time
            },
            "summary": self._compute_overall_metrics({}),
            "results": [
                {
                    "test_name": r.test_name,
                    "status": r.status.value,
                    "message": r.message,
                    "duration_ms": r.duration_ms,
                    "details": r.details if hasattr(r, 'details') else {}
                }
                for r in self.all_results
            ]
        }

        with open(output_file, 'w') as f:
            json.dump(results_data, f, indent=2)

        print(f"\nResults exported to: {output_file}")


class ContinuousTestingPipeline:
    """持续测试管道"""

    def __init__(self, registry: SkillRegistry):
        self.registry = registry
        self.runner = UnifiedTestRunner(registry)

    def run_on_skill_change(self, skill_name: str) -> bool:
        """当skill变更时运行测试"""
        print(f"\n🔄 Skill changed: {skill_name}")
        print("Running automated test pipeline...")

        results = self.runner.run_all_tests(
            skills_to_test=[skill_name],
            run_unit=True,
            run_integration=True,
            run_e2e=False,  # E2E tests may be too slow for every change
            detect_regression=True
        )

        # 检查是否通过
        metrics = self.runner._compute_overall_metrics(results)
        passed = metrics["failed"] == 0 and metrics["errors"] == 0

        if not passed:
            print(f"\n❌ Tests failed for {skill_name}")
            print("   Please fix the issues before committing")
            return False

        if results.get("regression", {}).get("has_regression"):
            print(f"\n⚠️  Regression detected in {skill_name}")
            print("   Please review the changes")
            return False

        print(f"\n✅ All tests passed for {skill_name}")
        return True

    def run_pre_commit_hook(self) -> bool:
        """运行pre-commit hook"""
        print("\n🪝 Running pre-commit tests...")

        results = self.runner.run_all_tests(
            run_unit=True,
            run_integration=True,
            run_e2e=False,
            detect_regression=True
        )

        metrics = self.runner._compute_overall_metrics(results)
        passed = metrics["failed"] == 0 and metrics["errors"] == 0

        if not passed:
            print("\n❌ Pre-commit tests failed")
            print("   Commit blocked - please fix failing tests")
            return False

        print("\n✅ Pre-commit tests passed")
        return True

    def run_nightly_tests(self):
        """运行夜间完整测试"""
        print("\n🌙 Running nightly test suite...")

        results = self.runner.run_all_tests(
            run_unit=True,
            run_integration=True,
            run_e2e=True,
            detect_regression=True
        )

        # 导出结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.runner.export_results(f"nightly_results_{timestamp}.json")

        # 发送通知（这里只是打印，实际可以发送email/slack等）
        metrics = self.runner._compute_overall_metrics(results)
        if metrics["failed"] > 0 or metrics["errors"] > 0:
            print("\n📧 Sending failure notification...")
            print(f"   Nightly tests failed: {metrics['failed']} failures, {metrics['errors']} errors")
        else:
            print("\n📧 Sending success notification...")
            print(f"   Nightly tests passed: {metrics['passed']}/{metrics['total_tests']}")


if __name__ == "__main__":
    # 示例用法
    from example_skills import create_skill_registry_with_examples

    print("Creating skill registry with example skills...")
    registry = create_skill_registry_with_examples()

    print("\nRunning unified test suite...")
    runner = UnifiedTestRunner(registry)

    # 运行所有测试
    results = runner.run_all_tests(
        run_unit=True,
        run_integration=False,  # 需要集成测试用例
        run_e2e=False,  # 需要E2E测试用例
        detect_regression=True
    )

    # 导出结果
    runner.export_results()
