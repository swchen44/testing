"""
Unit Test Framework for Skills
单元测试框架：验证skill描述、触发条件、参数定义等
"""
import json
from typing import List, Dict, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum
from skill_schema import Skill, TriggerRule, SkillParameter, SkillMetadata


class TestStatus(Enum):
    """测试状态"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    """测试结果"""
    test_name: str
    status: TestStatus
    message: str = ""
    details: Dict = field(default_factory=dict)
    duration_ms: float = 0.0


@dataclass
class UnitTestCase:
    """单元测试用例"""
    name: str
    description: str
    test_func: Callable
    setup: Optional[Callable] = None
    teardown: Optional[Callable] = None
    tags: List[str] = field(default_factory=list)


class SkillUnitTester:
    """Skill单元测试器"""

    def __init__(self, skill: Skill):
        self.skill = skill
        self.results: List[TestResult] = []

    def run_all_tests(self) -> List[TestResult]:
        """运行所有单元测试"""
        self.results = []

        # 测试metadata
        self.results.extend(self._test_metadata())

        # 测试triggers
        self.results.extend(self._test_triggers())

        # 测试parameters
        self.results.extend(self._test_parameters())

        # 测试skill完整性
        self.results.extend(self._test_skill_validity())

        return self.results

    def _test_metadata(self) -> List[TestResult]:
        """测试metadata完整性"""
        results = []

        # Test 1: Name存在且有效
        if self.skill.metadata.name:
            results.append(TestResult(
                test_name="test_metadata_name_exists",
                status=TestStatus.PASSED,
                message="Skill name is valid"
            ))
        else:
            results.append(TestResult(
                test_name="test_metadata_name_exists",
                status=TestStatus.FAILED,
                message="Skill name is missing or empty"
            ))

        # Test 2: Version格式有效
        if self.skill.metadata.version and self._is_valid_semver(self.skill.metadata.version):
            results.append(TestResult(
                test_name="test_metadata_version_valid",
                status=TestStatus.PASSED,
                message=f"Version {self.skill.metadata.version} is valid"
            ))
        else:
            results.append(TestResult(
                test_name="test_metadata_version_valid",
                status=TestStatus.FAILED,
                message="Version is missing or not in semver format"
            ))

        # Test 3: Description清晰且充分
        desc_len = len(self.skill.metadata.description) if self.skill.metadata.description else 0
        if desc_len >= 20:  # 至少20个字符
            results.append(TestResult(
                test_name="test_metadata_description_adequate",
                status=TestStatus.PASSED,
                message=f"Description length: {desc_len} chars"
            ))
        else:
            results.append(TestResult(
                test_name="test_metadata_description_adequate",
                status=TestStatus.FAILED,
                message=f"Description too short: {desc_len} chars (minimum 20)"
            ))

        # Test 4: Author信息存在
        if self.skill.metadata.author:
            results.append(TestResult(
                test_name="test_metadata_author_exists",
                status=TestStatus.PASSED,
                message=f"Author: {self.skill.metadata.author}"
            ))
        else:
            results.append(TestResult(
                test_name="test_metadata_author_exists",
                status=TestStatus.FAILED,
                message="Author information is missing"
            ))

        return results

    def _test_triggers(self) -> List[TestResult]:
        """测试触发条件"""
        results = []

        # Test 1: 至少有一个trigger
        if self.skill.triggers:
            results.append(TestResult(
                test_name="test_triggers_exist",
                status=TestStatus.PASSED,
                message=f"Found {len(self.skill.triggers)} trigger(s)"
            ))
        else:
            results.append(TestResult(
                test_name="test_triggers_exist",
                status=TestStatus.FAILED,
                message="No triggers defined"
            ))

        # Test 2: 每个trigger都有有效的pattern
        for idx, trigger in enumerate(self.skill.triggers):
            if trigger.pattern:
                results.append(TestResult(
                    test_name=f"test_trigger_{idx}_pattern_valid",
                    status=TestStatus.PASSED,
                    message=f"Trigger {idx} has pattern: '{trigger.pattern}'"
                ))
            else:
                results.append(TestResult(
                    test_name=f"test_trigger_{idx}_pattern_valid",
                    status=TestStatus.FAILED,
                    message=f"Trigger {idx} has empty pattern"
                ))

        # Test 3: Priority设置合理
        priorities = [t.priority for t in self.skill.triggers]
        if priorities and max(priorities) - min(priorities) <= 100:
            results.append(TestResult(
                test_name="test_triggers_priority_range",
                status=TestStatus.PASSED,
                message=f"Priority range: {min(priorities)}-{max(priorities)}"
            ))
        elif priorities:
            results.append(TestResult(
                test_name="test_triggers_priority_range",
                status=TestStatus.FAILED,
                message=f"Priority range too large: {min(priorities)}-{max(priorities)}"
            ))

        return results

    def _test_parameters(self) -> List[TestResult]:
        """测试参数定义"""
        results = []

        # Test 1: 参数名称唯一性
        param_names = [p.name for p in self.skill.parameters]
        if len(param_names) == len(set(param_names)):
            results.append(TestResult(
                test_name="test_parameters_unique_names",
                status=TestStatus.PASSED,
                message=f"All {len(param_names)} parameter names are unique"
            ))
        else:
            duplicates = [name for name in param_names if param_names.count(name) > 1]
            results.append(TestResult(
                test_name="test_parameters_unique_names",
                status=TestStatus.FAILED,
                message=f"Duplicate parameter names: {set(duplicates)}"
            ))

        # Test 2: 必需参数没有默认值
        for param in self.skill.parameters:
            if param.required and param.default is not None:
                results.append(TestResult(
                    test_name=f"test_parameter_{param.name}_no_default",
                    status=TestStatus.FAILED,
                    message=f"Required parameter '{param.name}' should not have default value"
                ))
            elif param.required:
                results.append(TestResult(
                    test_name=f"test_parameter_{param.name}_no_default",
                    status=TestStatus.PASSED,
                    message=f"Required parameter '{param.name}' has no default"
                ))

        # Test 3: 参数类型定义
        for param in self.skill.parameters:
            if param.type:
                results.append(TestResult(
                    test_name=f"test_parameter_{param.name}_has_type",
                    status=TestStatus.PASSED,
                    message=f"Parameter '{param.name}' has type: {param.type}"
                ))
            else:
                results.append(TestResult(
                    test_name=f"test_parameter_{param.name}_has_type",
                    status=TestStatus.FAILED,
                    message=f"Parameter '{param.name}' missing type definition"
                ))

        # Test 4: 参数描述
        for param in self.skill.parameters:
            if param.description and len(param.description) >= 10:
                results.append(TestResult(
                    test_name=f"test_parameter_{param.name}_has_description",
                    status=TestStatus.PASSED,
                    message=f"Parameter '{param.name}' has adequate description"
                ))
            else:
                results.append(TestResult(
                    test_name=f"test_parameter_{param.name}_has_description",
                    status=TestStatus.FAILED,
                    message=f"Parameter '{param.name}' missing or inadequate description"
                ))

        return results

    def _test_skill_validity(self) -> List[TestResult]:
        """测试skill整体有效性"""
        results = []

        # Test 1: Skill validate()方法
        validation_errors = self.skill.validate()
        if not validation_errors:
            results.append(TestResult(
                test_name="test_skill_validate",
                status=TestStatus.PASSED,
                message="Skill validation passed"
            ))
        else:
            results.append(TestResult(
                test_name="test_skill_validate",
                status=TestStatus.FAILED,
                message=f"Skill validation failed: {validation_errors}",
                details={"errors": validation_errors}
            ))

        # Test 2: Implementation或prompt_template存在
        if self.skill.implementation or self.skill.prompt_template:
            results.append(TestResult(
                test_name="test_skill_has_implementation",
                status=TestStatus.PASSED,
                message="Skill has implementation or prompt template"
            ))
        else:
            results.append(TestResult(
                test_name="test_skill_has_implementation",
                status=TestStatus.FAILED,
                message="Skill missing both implementation and prompt template"
            ))

        # Test 3: Examples存在且有效
        if self.skill.examples and len(self.skill.examples) > 0:
            results.append(TestResult(
                test_name="test_skill_has_examples",
                status=TestStatus.PASSED,
                message=f"Skill has {len(self.skill.examples)} example(s)"
            ))
        else:
            results.append(TestResult(
                test_name="test_skill_has_examples",
                status=TestStatus.FAILED,
                message="Skill should have at least one example"
            ))

        # Test 4: Red flags定义
        if self.skill.red_flags:
            results.append(TestResult(
                test_name="test_skill_has_red_flags",
                status=TestStatus.PASSED,
                message=f"Skill has {len(self.skill.red_flags)} red flag(s)"
            ))
        else:
            results.append(TestResult(
                test_name="test_skill_has_red_flags",
                status=TestStatus.FAILED,
                message="Skill should define red flags to prevent misuse"
            ))

        return results

    def _is_valid_semver(self, version: str) -> bool:
        """检查是否是有效的语义化版本号"""
        try:
            parts = version.split('.')
            if len(parts) != 3:
                return False
            for part in parts:
                int(part)
            return True
        except:
            return False

    def get_summary(self) -> Dict:
        """获取测试摘要"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "pass_rate": f"{(passed / total * 100):.2f}%" if total > 0 else "0%",
            "all_passed": failed == 0 and errors == 0
        }

    def print_results(self):
        """打印测试结果"""
        print("\n" + "=" * 70)
        print(f"UNIT TEST RESULTS FOR: {self.skill.metadata.name}")
        print("=" * 70)

        for result in self.results:
            status_symbol = {
                TestStatus.PASSED: "✅",
                TestStatus.FAILED: "❌",
                TestStatus.ERROR: "⚠️",
                TestStatus.SKIPPED: "⊝"
            }[result.status]

            print(f"{status_symbol} {result.test_name}")
            if result.message:
                print(f"   {result.message}")

        summary = self.get_summary()
        print("\n" + "=" * 70)
        print(f"SUMMARY: {summary['passed']}/{summary['total']} passed ({summary['pass_rate']})")
        print("=" * 70)


class TriggerTestSuite:
    """专门测试触发条件的测试套件"""

    def __init__(self, skill: Skill):
        self.skill = skill

    def test_trigger_matching(self, test_cases: List[Dict]) -> List[TestResult]:
        """
        测试触发条件匹配
        test_cases格式: [{"input": "...", "context": {...}, "should_trigger": True/False}]
        """
        results = []

        for idx, test_case in enumerate(test_cases):
            input_text = test_case.get("input", "")
            context = test_case.get("context")
            should_trigger = test_case.get("should_trigger", False)

            actual_trigger = self.skill.can_trigger(input_text, context)

            if actual_trigger == should_trigger:
                results.append(TestResult(
                    test_name=f"test_trigger_case_{idx}",
                    status=TestStatus.PASSED,
                    message=f"Trigger correctly {'matched' if should_trigger else 'ignored'}: '{input_text[:50]}...'",
                    details={"expected": should_trigger, "actual": actual_trigger}
                ))
            else:
                results.append(TestResult(
                    test_name=f"test_trigger_case_{idx}",
                    status=TestStatus.FAILED,
                    message=f"Trigger mismatch for: '{input_text[:50]}...'",
                    details={
                        "expected": should_trigger,
                        "actual": actual_trigger,
                        "input": input_text,
                        "context": context
                    }
                ))

        return results
