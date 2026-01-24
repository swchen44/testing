"""
Integration Test Framework for Skills
集成测试框架：验证skill调用、参数传递、返回值等
"""
import time
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from unit_test_framework import TestResult, TestStatus
from skill_schema import Skill, SkillRegistry


@dataclass
class IntegrationTestCase:
    """集成测试用例"""
    name: str
    description: str
    skill_name: str
    skill_version: Optional[str] = None
    input_params: Dict[str, Any] = field(default_factory=dict)
    expected_output: Any = None
    expected_output_type: Optional[str] = None
    should_succeed: bool = True
    timeout_ms: int = 5000
    context: Dict = field(default_factory=dict)


@dataclass
class SkillInvocation:
    """Skill调用记录"""
    skill_name: str
    skill_version: str
    parameters: Dict
    output: Any
    success: bool
    duration_ms: float
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


class SkillIntegrationTester:
    """Skill集成测试器"""

    def __init__(self, registry: SkillRegistry):
        self.registry = registry
        self.invocations: List[SkillInvocation] = []
        self.results: List[TestResult] = []

    def run_test_case(self, test_case: IntegrationTestCase) -> TestResult:
        """运行单个集成测试用例"""
        start_time = time.time()

        try:
            # 1. 查找skill
            skill = self.registry.get(test_case.skill_name, test_case.skill_version)
            if skill is None:
                return TestResult(
                    test_name=test_case.name,
                    status=TestStatus.ERROR,
                    message=f"Skill not found: {test_case.skill_name}",
                    duration_ms=(time.time() - start_time) * 1000
                )

            # 2. 执行skill
            try:
                output = skill.execute(**test_case.input_params)
                duration_ms = (time.time() - start_time) * 1000

                # 记录调用
                invocation = SkillInvocation(
                    skill_name=skill.metadata.name,
                    skill_version=skill.metadata.version,
                    parameters=test_case.input_params,
                    output=output,
                    success=True,
                    duration_ms=duration_ms
                )
                self.invocations.append(invocation)

                # 3. 验证输出
                if test_case.should_succeed:
                    validation_result = self._validate_output(
                        output,
                        test_case.expected_output,
                        test_case.expected_output_type
                    )

                    if validation_result["valid"]:
                        return TestResult(
                            test_name=test_case.name,
                            status=TestStatus.PASSED,
                            message=f"Skill executed successfully in {duration_ms:.2f}ms",
                            details={
                                "output": output,
                                "duration_ms": duration_ms,
                                "validation": validation_result
                            },
                            duration_ms=duration_ms
                        )
                    else:
                        return TestResult(
                            test_name=test_case.name,
                            status=TestStatus.FAILED,
                            message=f"Output validation failed: {validation_result['reason']}",
                            details={
                                "output": output,
                                "expected": test_case.expected_output,
                                "validation": validation_result
                            },
                            duration_ms=duration_ms
                        )
                else:
                    # 不应该成功但成功了
                    return TestResult(
                        test_name=test_case.name,
                        status=TestStatus.FAILED,
                        message="Skill should have failed but succeeded",
                        details={"output": output},
                        duration_ms=duration_ms
                    )

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000

                # 记录失败的调用
                invocation = SkillInvocation(
                    skill_name=skill.metadata.name,
                    skill_version=skill.metadata.version,
                    parameters=test_case.input_params,
                    output=None,
                    success=False,
                    duration_ms=duration_ms,
                    error=str(e)
                )
                self.invocations.append(invocation)

                if not test_case.should_succeed:
                    # 预期失败且确实失败了
                    return TestResult(
                        test_name=test_case.name,
                        status=TestStatus.PASSED,
                        message=f"Skill correctly failed: {str(e)}",
                        details={"error": str(e)},
                        duration_ms=duration_ms
                    )
                else:
                    # 不应该失败但失败了
                    return TestResult(
                        test_name=test_case.name,
                        status=TestStatus.FAILED,
                        message=f"Skill execution failed: {str(e)}",
                        details={"error": str(e)},
                        duration_ms=duration_ms
                    )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TestResult(
                test_name=test_case.name,
                status=TestStatus.ERROR,
                message=f"Test error: {str(e)}",
                details={"error": str(e)},
                duration_ms=duration_ms
            )

    def run_test_suite(self, test_cases: List[IntegrationTestCase]) -> List[TestResult]:
        """运行测试套件"""
        self.results = []

        for test_case in test_cases:
            result = self.run_test_case(test_case)
            self.results.append(result)

        return self.results

    def _validate_output(self, actual: Any, expected: Any, expected_type: Optional[str]) -> Dict:
        """验证输出"""
        # 类型检查
        if expected_type:
            actual_type = type(actual).__name__
            if actual_type != expected_type:
                return {
                    "valid": False,
                    "reason": f"Type mismatch: expected {expected_type}, got {actual_type}"
                }

        # 值检查
        if expected is not None:
            if actual == expected:
                return {"valid": True, "reason": "Output matches expected value"}
            else:
                return {
                    "valid": False,
                    "reason": f"Value mismatch: expected {expected}, got {actual}"
                }

        # 如果没有期望值，只要不抛异常就算通过
        return {"valid": True, "reason": "No expected value specified"}

    def test_parameter_validation(self, skill_name: str) -> List[TestResult]:
        """测试参数验证"""
        results = []
        skill = self.registry.get(skill_name)

        if not skill:
            return [TestResult(
                test_name="test_parameter_validation",
                status=TestStatus.ERROR,
                message=f"Skill not found: {skill_name}"
            )]

        # Test 1: 缺少必需参数
        required_params = [p for p in skill.parameters if p.required]
        if required_params:
            # 尝试不传参数执行
            try:
                skill.execute()
                results.append(TestResult(
                    test_name="test_missing_required_params",
                    status=TestStatus.FAILED,
                    message="Should have failed with missing required parameters"
                ))
            except (ValueError, TypeError) as e:
                results.append(TestResult(
                    test_name="test_missing_required_params",
                    status=TestStatus.PASSED,
                    message=f"Correctly rejected missing parameters: {str(e)}"
                ))

        # Test 2: 无效参数类型
        for param in skill.parameters[:3]:  # 测试前3个参数
            if param.type == "str":
                invalid_value = 12345
            elif param.type == "int":
                invalid_value = "not_an_int"
            elif param.type == "list":
                invalid_value = "not_a_list"
            else:
                continue

            try:
                params = {param.name: invalid_value}
                # 添加其他必需参数的默认值
                for other_param in skill.parameters:
                    if other_param.required and other_param.name != param.name:
                        params[other_param.name] = self._get_default_value(other_param.type)

                result = skill.execute(**params)
                # 如果有自定义验证，应该会失败
                if param.validation:
                    results.append(TestResult(
                        test_name=f"test_param_{param.name}_type_validation",
                        status=TestStatus.FAILED,
                        message=f"Should have rejected invalid type for {param.name}"
                    ))
            except Exception as e:
                results.append(TestResult(
                    test_name=f"test_param_{param.name}_type_validation",
                    status=TestStatus.PASSED,
                    message=f"Correctly rejected invalid type: {str(e)}"
                ))

        return results

    def test_skill_chaining(self, skill_chain: List[str], initial_params: Dict) -> TestResult:
        """
        测试多个skills的链式调用
        skill_chain: 按顺序调用的skill名称列表
        initial_params: 第一个skill的参数
        """
        start_time = time.time()
        outputs = []

        try:
            current_params = initial_params

            for idx, skill_name in enumerate(skill_chain):
                skill = self.registry.get(skill_name)
                if not skill:
                    return TestResult(
                        test_name="test_skill_chaining",
                        status=TestStatus.ERROR,
                        message=f"Skill not found in chain: {skill_name}",
                        duration_ms=(time.time() - start_time) * 1000
                    )

                output = skill.execute(**current_params)
                outputs.append({
                    "skill": skill_name,
                    "output": output
                })

                # 准备下一个skill的参数（简单示例：将输出作为下一个的输入）
                if idx < len(skill_chain) - 1:
                    current_params = {"input": output}

            duration_ms = (time.time() - start_time) * 1000
            return TestResult(
                test_name="test_skill_chaining",
                status=TestStatus.PASSED,
                message=f"Successfully chained {len(skill_chain)} skills",
                details={"outputs": outputs},
                duration_ms=duration_ms
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TestResult(
                test_name="test_skill_chaining",
                status=TestStatus.FAILED,
                message=f"Skill chaining failed: {str(e)}",
                details={"outputs": outputs, "error": str(e)},
                duration_ms=duration_ms
            )

    def _get_default_value(self, type_name: str) -> Any:
        """获取类型的默认值"""
        defaults = {
            "str": "",
            "int": 0,
            "float": 0.0,
            "bool": False,
            "list": [],
            "dict": {}
        }
        return defaults.get(type_name, None)

    def get_summary(self) -> Dict:
        """获取测试摘要"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)

        total_duration = sum(r.duration_ms for r in self.results)
        avg_duration = total_duration / total if total > 0 else 0

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "pass_rate": f"{(passed / total * 100):.2f}%" if total > 0 else "0%",
            "total_duration_ms": total_duration,
            "avg_duration_ms": avg_duration,
            "total_invocations": len(self.invocations),
            "successful_invocations": sum(1 for i in self.invocations if i.success)
        }

    def print_results(self):
        """打印测试结果"""
        print("\n" + "=" * 70)
        print("INTEGRATION TEST RESULTS")
        print("=" * 70)

        for result in self.results:
            status_symbol = {
                TestStatus.PASSED: "✅",
                TestStatus.FAILED: "❌",
                TestStatus.ERROR: "⚠️",
                TestStatus.SKIPPED: "⊝"
            }[result.status]

            print(f"{status_symbol} {result.test_name} ({result.duration_ms:.2f}ms)")
            if result.message:
                print(f"   {result.message}")

        summary = self.get_summary()
        print("\n" + "=" * 70)
        print(f"SUMMARY: {summary['passed']}/{summary['total']} passed ({summary['pass_rate']})")
        print(f"Average duration: {summary['avg_duration_ms']:.2f}ms")
        print(f"Total invocations: {summary['total_invocations']} ({summary['successful_invocations']} successful)")
        print("=" * 70)


class PerformanceTester:
    """性能测试器"""

    def __init__(self, registry: SkillRegistry):
        self.registry = registry

    def benchmark_skill(self, skill_name: str, params: Dict, iterations: int = 100) -> Dict:
        """性能基准测试"""
        skill = self.registry.get(skill_name)
        if not skill:
            return {"error": f"Skill not found: {skill_name}"}

        durations = []
        errors = 0

        for _ in range(iterations):
            start = time.time()
            try:
                skill.execute(**params)
                duration = (time.time() - start) * 1000
                durations.append(duration)
            except Exception as e:
                errors += 1

        if not durations:
            return {"error": "All iterations failed"}

        return {
            "skill": skill_name,
            "iterations": iterations,
            "successful": len(durations),
            "failed": errors,
            "min_ms": min(durations),
            "max_ms": max(durations),
            "avg_ms": sum(durations) / len(durations),
            "median_ms": sorted(durations)[len(durations) // 2],
            "p95_ms": sorted(durations)[int(len(durations) * 0.95)],
            "p99_ms": sorted(durations)[int(len(durations) * 0.99)]
        }
