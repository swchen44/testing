# Enterprise Agent Skill Testing Framework

一个系统化、企业级的Agent Skill测试框架，支持单元测试、集成测试、端到端测试和回归检测。

## 核心理念

基于OpenAI的Eval-Driven Development和业界最佳实践，这个框架提供：

1. **三层测试金字塔**
   - 单元测试：验证skill定义、触发条件、参数
   - 集成测试：验证skill调用、参数传递、返回值
   - 端到端测试：验证真实项目中的完整工作流

2. **回归检测**
   - 自动对比baseline指标
   - 检测性能退化
   - 追踪质量趋势

3. **持续测试管道**
   - Pre-commit hooks
   - On-change testing
   - Nightly test suites

## 架构

```
skill_testing_framework/
├── skill_schema.py              # Skill定义数据结构
├── unit_test_framework.py       # 单元测试框架
├── integration_test_framework.py # 集成测试框架
├── e2e_test_framework.py        # 端到端测试框架
├── test_runner.py               # 统一测试运行器
├── example_skills.py            # 示例skills
└── README.md                    # 本文档
```

## 快速开始

### 1. 定义Skill

```python
from skill_schema import (
    Skill, SkillMetadata, SkillType,
    TriggerRule, TriggerCondition,
    SkillParameter, SkillOutput
)

def my_implementation(param1: str, param2: int = 10) -> dict:
    """Skill实现逻辑"""
    return {"result": f"{param1} x {param2}"}

my_skill = Skill(
    metadata=SkillMetadata(
        name="my-skill",
        version="1.0.0",
        description="A sample skill for demonstration",
        skill_type=SkillType.TOOL,
        author="Your Name",
        created_at="2025-01-24",
        updated_at="2025-01-24"
    ),
    triggers=[
        TriggerRule(
            condition_type=TriggerCondition.KEYWORD,
            pattern="do something",
            priority=10
        )
    ],
    parameters=[
        SkillParameter(
            name="param1",
            type="str",
            required=True,
            description="First parameter"
        ),
        SkillParameter(
            name="param2",
            type="int",
            required=False,
            default=10,
            description="Second parameter"
        )
    ],
    output=SkillOutput(
        type="dict",
        schema={"result": "str"}
    ),
    implementation=my_implementation,
    examples=[{"input": {"param1": "test"}, "output": {"result": "test x 10"}}],
    red_flags=["Don't use without validation"]
)
```

### 2. 注册Skill

```python
from skill_schema import SkillRegistry

registry = SkillRegistry()
registry.register(my_skill)
```

### 3. 运行单元测试

```python
from unit_test_framework import SkillUnitTester

tester = SkillUnitTester(my_skill)
results = tester.run_all_tests()
tester.print_results()
```

输出示例：
```
======================================================================
UNIT TEST RESULTS FOR: my-skill
======================================================================
✅ test_metadata_name_exists
   Skill name is valid
✅ test_metadata_version_valid
   Version 1.0.0 is valid
✅ test_metadata_description_adequate
   Description length: 35 chars
...
======================================================================
SUMMARY: 12/12 passed (100.00%)
======================================================================
```

### 4. 运行集成测试

```python
from integration_test_framework import (
    SkillIntegrationTester,
    IntegrationTestCase
)

# 定义测试用例
test_cases = [
    IntegrationTestCase(
        name="test_basic_execution",
        description="Test basic skill execution",
        skill_name="my-skill",
        input_params={"param1": "hello"},
        expected_output={"result": "hello x 10"},
        should_succeed=True
    ),
    IntegrationTestCase(
        name="test_missing_param",
        description="Test missing required parameter",
        skill_name="my-skill",
        input_params={},
        should_succeed=False  # 应该失败
    )
]

tester = SkillIntegrationTester(registry)
results = tester.run_test_suite(test_cases)
tester.print_results()
```

### 5. 运行端到端测试

```python
from e2e_test_framework import E2ETestRunner, E2ETestCase, WorkflowStep

# 定义工作流
e2e_test = E2ETestCase(
    name="test_code_review_workflow",
    description="Test complete code review workflow",
    workflow=[
        WorkflowStep(
            name="generate_code",
            skill_name="code-generator",
            input_params={"spec": "create hello world function"}
        ),
        WorkflowStep(
            name="review_code",
            skill_name="code-review",
            input_params={"code": "${generate_code.output}", "language": "python"}
        ),
        WorkflowStep(
            name="generate_tests",
            skill_name="test-generator",
            input_params={"function_name": "hello_world", "function_code": "${generate_code.output}"}
        )
    ],
    expected_files=["tests/test_hello_world.py"],
    validation_commands=["pytest tests/"]
)

runner = E2ETestRunner(registry)
result = runner.run_test_case(e2e_test)
```

### 6. 统一测试运行器

```python
from test_runner import UnifiedTestRunner

runner = UnifiedTestRunner(registry)

results = runner.run_all_tests(
    run_unit=True,
    run_integration=True,
    run_e2e=True,
    detect_regression=True
)

# 导出结果
runner.export_results("test_results.json")
```

## 高级功能

### 触发条件测试

```python
from unit_test_framework import TriggerTestSuite

trigger_suite = TriggerTestSuite(my_skill)

test_cases = [
    {"input": "please do something", "should_trigger": True},
    {"input": "do something else", "should_trigger": True},
    {"input": "unrelated command", "should_trigger": False},
    {
        "input": "context-based trigger",
        "context": {"action": "review"},
        "should_trigger": True
    }
]

results = trigger_suite.test_trigger_matching(test_cases)
```

### 性能基准测试

```python
from integration_test_framework import PerformanceTester

perf_tester = PerformanceTester(registry)

benchmark = perf_tester.benchmark_skill(
    skill_name="my-skill",
    params={"param1": "test"},
    iterations=100
)

print(f"Average: {benchmark['avg_ms']:.2f}ms")
print(f"P95: {benchmark['p95_ms']:.2f}ms")
print(f"P99: {benchmark['p99_ms']:.2f}ms")
```

### Skill链式调用测试

```python
from integration_test_framework import SkillIntegrationTester

tester = SkillIntegrationTester(registry)

result = tester.test_skill_chaining(
    skill_chain=["skill-a", "skill-b", "skill-c"],
    initial_params={"input": "start"}
)
```

### 回归检测

```python
from e2e_test_framework import RegressionDetector

detector = RegressionDetector()

# 运行测试并获取指标
metrics = {
    "total_tests": 50,
    "passed": 48,
    "failed": 2,
    "pass_rate": "96.00%",
    "avg_duration_ms": 125.5
}

# 检测回归
regression_result = detector.detect_regression(metrics)

if regression_result["has_regression"]:
    print("⚠️  Regression detected!")
    for reg in regression_result["regressions"]:
        print(f"  {reg['metric']}: {reg['baseline']} → {reg['current']}")
else:
    print("✅ No regression")
```

### 持续集成

```python
from test_runner import ContinuousTestingPipeline

pipeline = ContinuousTestingPipeline(registry)

# Pre-commit hook
if not pipeline.run_pre_commit_hook():
    exit(1)  # 阻止commit

# On skill change
pipeline.run_on_skill_change("my-skill")

# Nightly tests
pipeline.run_nightly_tests()
```

## 测试最佳实践

### 1. Skill定义质量标准

✅ **必须满足**：
- 清晰的metadata（name, version, description, author）
- 语义化版本号（semver）
- 至少一个触发条件
- 完整的参数定义（type, description）
- 输出schema定义
- 至少一个example
- 明确的red flags

❌ **避免**：
- 模糊的描述
- 缺少参数验证
- 没有examples
- 忽略error handling

### 2. 单元测试覆盖

单元测试应该验证：
- ✅ Metadata完整性
- ✅ 触发条件正确性
- ✅ 参数定义合理性
- ✅ 必需参数验证
- ✅ 输出schema定义

### 3. 集成测试场景

集成测试应该包含：
- ✅ 正常执行路径
- ✅ 异常输入处理
- ✅ 参数验证
- ✅ 边界条件
- ✅ 性能基准

### 4. 端到端测试设计

E2E测试应该模拟：
- ✅ 真实的用户工作流
- ✅ 多个skills的协作
- ✅ 文件系统操作
- ✅ Git操作
- ✅ 外部命令执行

### 5. 回归预防

**每次修改skill后必须**：
1. 运行完整单元测试
2. 运行相关集成测试
3. 检查回归指标
4. 更新baseline（如果intentional changes）
5. Code review检查测试覆盖

## CI/CD集成

### GitHub Actions示例

```yaml
name: Skill Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Run Unit Tests
        run: python test_runner.py --unit-only

      - name: Run Integration Tests
        run: python test_runner.py --integration-only

      - name: Check Regression
        run: python test_runner.py --regression-check

      - name: Upload Results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: test_results.json
```

### Pre-commit Hook

创建 `.git/hooks/pre-commit`:

```bash
#!/bin/bash
python -c "
from test_runner import ContinuousTestingPipeline
from example_skills import create_skill_registry_with_examples

registry = create_skill_registry_with_examples()
pipeline = ContinuousTestingPipeline(registry)

if not pipeline.run_pre_commit_hook():
    exit(1)
"
```

## 指标追踪

框架自动追踪以下指标：

- **Pass Rate**: 测试通过率
- **Duration**: 执行时间（平均、P95、P99）
- **Coverage**: 测试覆盖的skills数量
- **Regression**: 与baseline的对比

指标保存在 `baseline_metrics.json`:

```json
{
  "total_tests": 50,
  "passed": 48,
  "failed": 2,
  "errors": 0,
  "pass_rate": "96.00%",
  "total_duration_ms": 6275.5,
  "avg_duration_ms": 125.51,
  "timestamp": "2025-01-24T10:30:00"
}
```

## 常见问题

### Q: 如何调试失败的E2E测试？

E2E测试会保留临时目录，可以检查：
```python
result = runner.run_test_case(e2e_test)
print(f"Project dir: {result.details['project_dir']}")
# 进入目录检查文件和git历史
```

### Q: 如何加速测试执行？

1. 使用并行测试执行
2. E2E测试只在CI/CD运行，本地开发只跑单元+集成
3. 使用缓存机制
4. 按需运行（只测试修改的skills）

### Q: 如何处理外部依赖？

使用mock和fixture：
```python
def test_with_mock():
    with mock.patch('external_api.call') as mock_call:
        mock_call.return_value = {"status": "ok"}
        # run test
```

## 贡献指南

添加新的测试类型：

1. 在相应的框架文件中添加测试类
2. 在`test_runner.py`中集成
3. 添加示例到`example_skills.py`
4. 更新文档

## 许可

MIT License

## 参考资料

- [OpenAI Eval-Driven Development](https://developers.openai.com/blog/eval-skills/)
- [Superpowers Testing Framework](https://github.com/obra/superpowers/tree/main/tests)
- [Anthropic Agent Skills Standard](https://agent-skills.md/)
