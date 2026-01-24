"""
End-to-End Test Framework for Skills
端到端测试框架：验证真实项目中的完整工作流
"""
import os
import time
import json
import subprocess
import tempfile
import shutil
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path
from unit_test_framework import TestResult, TestStatus
from skill_schema import Skill, SkillRegistry


@dataclass
class WorkflowStep:
    """工作流步骤"""
    name: str
    skill_name: str
    input_params: Dict[str, Any] = field(default_factory=dict)
    expected_outcome: Optional[str] = None
    validation_func: Optional[Callable] = None
    timeout_ms: int = 30000


@dataclass
class E2ETestCase:
    """端到端测试用例"""
    name: str
    description: str
    workflow: List[WorkflowStep]
    setup_func: Optional[Callable] = None
    teardown_func: Optional[Callable] = None
    project_template: Optional[str] = None  # 项目模板目录
    environment: Dict[str, str] = field(default_factory=dict)
    expected_files: List[str] = field(default_factory=list)  # 期望生成的文件
    expected_git_commits: int = 0  # 期望的git提交数
    validation_commands: List[str] = field(default_factory=list)  # 验证命令（如运行测试）


@dataclass
class WorkflowExecution:
    """工作流执行记录"""
    test_name: str
    steps_completed: List[str] = field(default_factory=list)
    steps_failed: List[str] = field(default_factory=list)
    outputs: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    success: bool = False
    error: Optional[str] = None


class E2ETestRunner:
    """端到端测试运行器"""

    def __init__(self, registry: SkillRegistry):
        self.registry = registry
        self.results: List[TestResult] = []
        self.executions: List[WorkflowExecution] = []

    def run_test_case(self, test_case: E2ETestCase) -> TestResult:
        """运行端到端测试用例"""
        start_time = time.time()
        temp_dir = None
        execution = WorkflowExecution(test_name=test_case.name)

        try:
            # 1. 设置测试环境
            temp_dir = self._setup_environment(test_case)

            # 2. 运行setup
            if test_case.setup_func:
                test_case.setup_func(temp_dir)

            # 3. 执行workflow
            workflow_result = self._execute_workflow(
                test_case.workflow,
                temp_dir,
                execution
            )

            if not workflow_result["success"]:
                return TestResult(
                    test_name=test_case.name,
                    status=TestStatus.FAILED,
                    message=f"Workflow failed: {workflow_result['error']}",
                    details={"execution": execution},
                    duration_ms=(time.time() - start_time) * 1000
                )

            # 4. 验证结果
            validation_result = self._validate_outcome(test_case, temp_dir, execution)

            if validation_result["valid"]:
                execution.success = True
                self.executions.append(execution)

                return TestResult(
                    test_name=test_case.name,
                    status=TestStatus.PASSED,
                    message=f"E2E test passed: {validation_result['message']}",
                    details={
                        "execution": execution,
                        "validation": validation_result,
                        "project_dir": temp_dir
                    },
                    duration_ms=(time.time() - start_time) * 1000
                )
            else:
                execution.error = validation_result["reason"]
                self.executions.append(execution)

                return TestResult(
                    test_name=test_case.name,
                    status=TestStatus.FAILED,
                    message=f"Validation failed: {validation_result['reason']}",
                    details={
                        "execution": execution,
                        "validation": validation_result,
                        "project_dir": temp_dir
                    },
                    duration_ms=(time.time() - start_time) * 1000
                )

        except Exception as e:
            execution.error = str(e)
            self.executions.append(execution)

            return TestResult(
                test_name=test_case.name,
                status=TestStatus.ERROR,
                message=f"E2E test error: {str(e)}",
                details={"execution": execution, "error": str(e)},
                duration_ms=(time.time() - start_time) * 1000
            )

        finally:
            # 5. 运行teardown
            if test_case.teardown_func and temp_dir:
                try:
                    test_case.teardown_func(temp_dir)
                except Exception as e:
                    print(f"Teardown error: {e}")

            # 6. 清理（可选保留用于调试）
            # if temp_dir and os.path.exists(temp_dir):
            #     shutil.rmtree(temp_dir)

    def _setup_environment(self, test_case: E2ETestCase) -> str:
        """设置测试环境"""
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix=f"e2e_test_{test_case.name}_")

        # 如果有项目模板，复制到临时目录
        if test_case.project_template and os.path.exists(test_case.project_template):
            for item in os.listdir(test_case.project_template):
                src = os.path.join(test_case.project_template, item)
                dst = os.path.join(temp_dir, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)

        # 初始化git仓库
        subprocess.run(
            ["git", "init"],
            cwd=temp_dir,
            capture_output=True,
            check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=temp_dir,
            capture_output=True,
            check=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=temp_dir,
            capture_output=True,
            check=True
        )

        return temp_dir

    def _execute_workflow(
        self,
        workflow: List[WorkflowStep],
        project_dir: str,
        execution: WorkflowExecution
    ) -> Dict:
        """执行工作流"""
        os.chdir(project_dir)

        for step in workflow:
            try:
                # 获取skill
                skill = self.registry.get(step.skill_name)
                if not skill:
                    return {
                        "success": False,
                        "error": f"Skill not found: {step.skill_name}"
                    }

                # 执行skill
                step_start = time.time()

                # 注入项目上下文
                params = step.input_params.copy()
                params["_project_dir"] = project_dir

                output = skill.execute(**params)

                step_duration = (time.time() - step_start) * 1000

                # 记录结果
                execution.steps_completed.append(step.name)
                execution.outputs[step.name] = {
                    "output": output,
                    "duration_ms": step_duration
                }

                # 步骤级验证
                if step.validation_func:
                    if not step.validation_func(output, project_dir):
                        execution.steps_failed.append(step.name)
                        return {
                            "success": False,
                            "error": f"Step validation failed: {step.name}"
                        }

            except Exception as e:
                execution.steps_failed.append(step.name)
                return {
                    "success": False,
                    "error": f"Step '{step.name}' failed: {str(e)}"
                }

        return {"success": True}

    def _validate_outcome(
        self,
        test_case: E2ETestCase,
        project_dir: str,
        execution: WorkflowExecution
    ) -> Dict:
        """验证测试结果"""
        validations = []

        # 1. 验证期望的文件是否存在
        if test_case.expected_files:
            for expected_file in test_case.expected_files:
                file_path = os.path.join(project_dir, expected_file)
                if os.path.exists(file_path):
                    validations.append({
                        "type": "file_exists",
                        "item": expected_file,
                        "valid": True
                    })
                else:
                    return {
                        "valid": False,
                        "reason": f"Expected file not found: {expected_file}",
                        "validations": validations
                    }

        # 2. 验证git提交数
        if test_case.expected_git_commits > 0:
            try:
                result = subprocess.run(
                    ["git", "rev-list", "--count", "HEAD"],
                    cwd=project_dir,
                    capture_output=True,
                    text=True,
                    check=True
                )
                commit_count = int(result.stdout.strip())

                if commit_count >= test_case.expected_git_commits:
                    validations.append({
                        "type": "git_commits",
                        "expected": test_case.expected_git_commits,
                        "actual": commit_count,
                        "valid": True
                    })
                else:
                    return {
                        "valid": False,
                        "reason": f"Expected {test_case.expected_git_commits} commits, got {commit_count}",
                        "validations": validations
                    }
            except Exception as e:
                return {
                    "valid": False,
                    "reason": f"Failed to check git commits: {str(e)}",
                    "validations": validations
                }

        # 3. 运行验证命令
        if test_case.validation_commands:
            for cmd in test_case.validation_commands:
                try:
                    result = subprocess.run(
                        cmd,
                        shell=True,
                        cwd=project_dir,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if result.returncode == 0:
                        validations.append({
                            "type": "command",
                            "command": cmd,
                            "valid": True,
                            "output": result.stdout
                        })
                    else:
                        return {
                            "valid": False,
                            "reason": f"Validation command failed: {cmd}",
                            "output": result.stderr,
                            "validations": validations
                        }
                except subprocess.TimeoutExpired:
                    return {
                        "valid": False,
                        "reason": f"Validation command timeout: {cmd}",
                        "validations": validations
                    }
                except Exception as e:
                    return {
                        "valid": False,
                        "reason": f"Validation command error: {str(e)}",
                        "validations": validations
                    }

        return {
            "valid": True,
            "message": f"All validations passed ({len(validations)} checks)",
            "validations": validations
        }

    def run_test_suite(self, test_cases: List[E2ETestCase]) -> List[TestResult]:
        """运行测试套件"""
        self.results = []

        for test_case in test_cases:
            print(f"\nRunning E2E test: {test_case.name}...")
            result = self.run_test_case(test_case)
            self.results.append(result)

        return self.results

    def get_summary(self) -> Dict:
        """获取测试摘要"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)

        total_duration = sum(r.duration_ms for r in self.results)

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "pass_rate": f"{(passed / total * 100):.2f}%" if total > 0 else "0%",
            "total_duration_ms": total_duration,
            "total_workflows": len(self.executions),
            "successful_workflows": sum(1 for e in self.executions if e.success)
        }

    def print_results(self):
        """打印测试结果"""
        print("\n" + "=" * 70)
        print("END-TO-END TEST RESULTS")
        print("=" * 70)

        for result in self.results:
            status_symbol = {
                TestStatus.PASSED: "✅",
                TestStatus.FAILED: "❌",
                TestStatus.ERROR: "⚠️",
                TestStatus.SKIPPED: "⊝"
            }[result.status]

            print(f"\n{status_symbol} {result.test_name}")
            print(f"   Duration: {result.duration_ms / 1000:.2f}s")
            if result.message:
                print(f"   {result.message}")

            # 显示workflow执行详情
            if "execution" in result.details:
                execution = result.details["execution"]
                if isinstance(execution, dict):
                    steps_completed = execution.get("steps_completed", [])
                    steps_failed = execution.get("steps_failed", [])
                else:
                    steps_completed = execution.steps_completed
                    steps_failed = execution.steps_failed

                if steps_completed:
                    print(f"   Completed steps: {', '.join(steps_completed)}")
                if steps_failed:
                    print(f"   Failed steps: {', '.join(steps_failed)}")

        summary = self.get_summary()
        print("\n" + "=" * 70)
        print(f"SUMMARY: {summary['passed']}/{summary['total']} passed ({summary['pass_rate']})")
        print(f"Total duration: {summary['total_duration_ms'] / 1000:.2f}s")
        print(f"Workflows: {summary['successful_workflows']}/{summary['total_workflows']} successful")
        print("=" * 70)


class RegressionDetector:
    """回归检测器"""

    def __init__(self):
        self.baseline_file = "baseline_metrics.json"

    def save_baseline(self, metrics: Dict):
        """保存基线指标"""
        with open(self.baseline_file, 'w') as f:
            json.dump(metrics, f, indent=2)

    def load_baseline(self) -> Optional[Dict]:
        """加载基线指标"""
        if os.path.exists(self.baseline_file):
            with open(self.baseline_file, 'r') as f:
                return json.load(f)
        return None

    def detect_regression(self, current_metrics: Dict) -> Dict:
        """检测回归"""
        baseline = self.load_baseline()

        if not baseline:
            return {
                "has_regression": False,
                "message": "No baseline found, saving current as baseline",
                "action": "save_baseline"
            }

        regressions = []

        # 比较pass rate
        baseline_pass_rate = float(baseline.get("pass_rate", "0%").rstrip('%'))
        current_pass_rate = float(current_metrics.get("pass_rate", "0%").rstrip('%'))

        if current_pass_rate < baseline_pass_rate - 5:  # 下降超过5%
            regressions.append({
                "metric": "pass_rate",
                "baseline": f"{baseline_pass_rate}%",
                "current": f"{current_pass_rate}%",
                "change": f"{current_pass_rate - baseline_pass_rate:.2f}%"
            })

        # 比较平均执行时间
        if "avg_duration_ms" in baseline and "avg_duration_ms" in current_metrics:
            baseline_duration = baseline["avg_duration_ms"]
            current_duration = current_metrics["avg_duration_ms"]

            if current_duration > baseline_duration * 1.5:  # 增加超过50%
                regressions.append({
                    "metric": "avg_duration_ms",
                    "baseline": f"{baseline_duration:.2f}ms",
                    "current": f"{current_duration:.2f}ms",
                    "change": f"+{((current_duration / baseline_duration - 1) * 100):.2f}%"
                })

        if regressions:
            return {
                "has_regression": True,
                "message": f"Detected {len(regressions)} regression(s)",
                "regressions": regressions
            }
        else:
            return {
                "has_regression": False,
                "message": "No regressions detected",
                "improvements": self._detect_improvements(baseline, current_metrics)
            }

    def _detect_improvements(self, baseline: Dict, current: Dict) -> List[Dict]:
        """检测改进"""
        improvements = []

        # 检查pass rate提升
        baseline_pass_rate = float(baseline.get("pass_rate", "0%").rstrip('%'))
        current_pass_rate = float(current.get("pass_rate", "0%").rstrip('%'))

        if current_pass_rate > baseline_pass_rate + 2:
            improvements.append({
                "metric": "pass_rate",
                "improvement": f"+{current_pass_rate - baseline_pass_rate:.2f}%"
            })

        return improvements
