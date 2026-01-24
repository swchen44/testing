# 快速入门指南

## 5分钟上手企业级Skill测试

### 步骤1: 安装依赖（可选）

```bash
pip install -r requirements.txt
```

注：核心功能使用Python标准库，不需要额外依赖即可运行

### 步骤2: 运行演示

```bash
python3 demo.py
```

这将展示完整的测试流程：
- ✅ 单元测试
- ✅ 触发条件测试
- ✅ 集成测试
- ✅ 性能测试
- ✅ 回归检测
- ✅ 统一测试运行器
- ✅ CI/CD集成

### 步骤3: 查看示例Skill

```bash
python3 example_skills.py
```

输出：
```
Registered Skills:
  - code-review v1.0.0: Automated code review skill
  - test-generator v1.0.0: Generate unit tests automatically
  - refactor v1.0.0: Refactor code to improve quality

Testing code-review skill:
Review result: {'language': 'python', 'issues': [], ...}
```

### 步骤4: 创建你的第一个Skill

创建 `my_first_skill.py`:

```python
from skill_schema import *

def my_implementation(input_text: str) -> str:
    """处理输入文本"""
    return f"Processed: {input_text}"

my_skill = Skill(
    metadata=SkillMetadata(
        name="my-first-skill",
        version="1.0.0",
        description="My first enterprise skill",
        skill_type=SkillType.TOOL,
        author="Your Name",
        created_at="2025-01-24",
        updated_at="2025-01-24"
    ),
    triggers=[
        TriggerRule(
            condition_type=TriggerCondition.KEYWORD,
            pattern="process text",
            priority=10
        )
    ],
    parameters=[
        SkillParameter(
            name="input_text",
            type="str",
            required=True,
            description="Text to process"
        )
    ],
    output=SkillOutput(
        type="str",
        schema={"type": "string"}
    ),
    implementation=my_implementation,
    examples=[
        {"input": {"input_text": "hello"}, "output": "Processed: hello"}
    ],
    red_flags=["Don't process sensitive data"]
)

# 测试
from unit_test_framework import SkillUnitTester

tester = SkillUnitTester(my_skill)
results = tester.run_all_tests()
tester.print_results()
```

运行：
```bash
python3 my_first_skill.py
```

### 步骤5: 编写测试用例

创建 `test_my_skill.py`:

```python
from skill_schema import SkillRegistry
from integration_test_framework import *
from my_first_skill import my_skill

# 注册skill
registry = SkillRegistry()
registry.register(my_skill)

# 集成测试
test_cases = [
    IntegrationTestCase(
        name="test_basic",
        description="Basic functionality test",
        skill_name="my-first-skill",
        input_params={"input_text": "hello world"},
        expected_output="Processed: hello world",
        should_succeed=True
    )
]

tester = SkillIntegrationTester(registry)
results = tester.run_test_suite(test_cases)
tester.print_results()
```

### 步骤6: 运行完整测试套件

创建 `run_tests.py`:

```python
from test_runner import UnifiedTestRunner
from skill_schema import SkillRegistry
from my_first_skill import my_skill

# 注册
registry = SkillRegistry()
registry.register(my_skill)

# 运行测试
runner = UnifiedTestRunner(registry)
results = runner.run_all_tests(
    run_unit=True,
    run_integration=True,
    detect_regression=True
)

# 导出结果
runner.export_results("my_test_results.json")
```

## 常用命令

### 运行单元测试
```python
from unit_test_framework import SkillUnitTester
tester = SkillUnitTester(my_skill)
tester.run_all_tests()
tester.print_results()
```

### 运行集成测试
```python
from integration_test_framework import SkillIntegrationTester
tester = SkillIntegrationTester(registry)
tester.run_test_suite(test_cases)
```

### 性能基准测试
```python
from integration_test_framework import PerformanceTester
perf = PerformanceTester(registry)
benchmark = perf.benchmark_skill("my-skill", params, iterations=100)
```

### 回归检测
```python
from e2e_test_framework import RegressionDetector
detector = RegressionDetector()
detector.save_baseline(metrics)
result = detector.detect_regression(current_metrics)
```

## 项目结构建议

```
your_project/
├── skills/
│   ├── __init__.py
│   ├── skill_a.py
│   ├── skill_b.py
│   └── skill_c.py
├── tests/
│   ├── unit/
│   │   ├── test_skill_a.py
│   │   ├── test_skill_b.py
│   │   └── test_skill_c.py
│   ├── integration/
│   │   └── test_integration.py
│   └── e2e/
│       └── test_workflows.py
├── skill_testing_framework/  # 这个框架
│   ├── skill_schema.py
│   ├── unit_test_framework.py
│   ├── integration_test_framework.py
│   ├── e2e_test_framework.py
│   └── test_runner.py
└── run_all_tests.py
```

## 下一步

1. 阅读完整文档：`README.md`
2. 查看示例：`example_skills.py`
3. 运行演示：`demo.py`
4. 创建自己的skill
5. 编写测试用例
6. 集成到CI/CD

## 核心概念

### Skill定义包含：
- ✅ **Metadata**: 名称、版本、描述
- ✅ **Triggers**: 触发条件
- ✅ **Parameters**: 参数定义
- ✅ **Output**: 输出schema
- ✅ **Implementation**: 实现逻辑
- ✅ **Examples**: 使用示例
- ✅ **Red Flags**: 禁止事项

### 测试层级：
1. **单元测试**: 验证skill定义（秒级）
2. **集成测试**: 验证skill执行（秒-分钟级）
3. **端到端测试**: 验证完整工作流（分钟级）

### 质量保障：
- 📊 **性能基准**: 追踪执行速度
- 🔍 **回归检测**: 自动发现质量下降
- 🔄 **持续测试**: CI/CD集成
- 📈 **趋势分析**: 长期质量追踪

## 获取帮助

- 完整文档：`README.md`
- 示例代码：`example_skills.py`
- 演示程序：`demo.py`

## 企业级最佳实践

✅ **必须做的**：
1. 每个skill都要有完整的单元测试
2. 关键skill需要集成测试
3. 重要工作流需要E2E测试
4. 建立性能baseline
5. 启用回归检测
6. 集成到CI/CD

❌ **避免的**：
1. 没有测试就部署skill
2. 忽略测试失败
3. 跳过回归检测
4. 没有性能基准
5. 测试覆盖不足
6. 缺少文档

开始构建你的企业级Agent Skills吧！
