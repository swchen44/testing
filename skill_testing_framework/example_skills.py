"""
示例Skills定义
展示如何创建可测试的企业级skills
"""
from skill_schema import (
    Skill, SkillMetadata, SkillType, TriggerRule, TriggerCondition,
    SkillParameter, SkillOutput, SkillRegistry
)


def create_code_review_skill() -> Skill:
    """创建代码审查skill"""

    def implementation(code: str, language: str = "python", _project_dir: str = None) -> dict:
        """代码审查实现"""
        issues = []
        suggestions = []

        # 简单的代码审查逻辑
        if not code.strip():
            issues.append("Code is empty")

        if language == "python":
            if "TODO" in code:
                suggestions.append("Found TODO comments - consider addressing them")
            if "print(" in code and "debug" in code.lower():
                suggestions.append("Debug print statements should be removed")
            if len(code.split('\n')) > 100:
                suggestions.append("Function is too long - consider breaking it down")

        return {
            "language": language,
            "issues": issues,
            "suggestions": suggestions,
            "approved": len(issues) == 0,
            "quality_score": max(0, 100 - len(issues) * 20 - len(suggestions) * 5)
        }

    return Skill(
        metadata=SkillMetadata(
            name="code-review",
            version="1.0.0",
            description="Automated code review skill that analyzes code quality and provides feedback",
            skill_type=SkillType.ANALYSIS,
            author="Enterprise Team",
            created_at="2025-01-01",
            updated_at="2025-01-01",
            tags=["code-quality", "review", "analysis"]
        ),
        triggers=[
            TriggerRule(
                condition_type=TriggerCondition.KEYWORD,
                pattern="review code",
                priority=10
            ),
            TriggerRule(
                condition_type=TriggerCondition.KEYWORD,
                pattern="code review",
                priority=10
            ),
            TriggerRule(
                condition_type=TriggerCondition.CONTEXT,
                pattern="review_required",
                priority=5,
                context_requirements={"action": "review"}
            )
        ],
        parameters=[
            SkillParameter(
                name="code",
                type="str",
                required=True,
                description="The code to review"
            ),
            SkillParameter(
                name="language",
                type="str",
                required=False,
                default="python",
                description="Programming language of the code"
            ),
            SkillParameter(
                name="_project_dir",
                type="str",
                required=False,
                description="Project directory (injected by framework)"
            )
        ],
        output=SkillOutput(
            type="dict",
            schema={
                "issues": "list",
                "suggestions": "list",
                "approved": "bool",
                "quality_score": "int"
            },
            examples=[
                {
                    "issues": [],
                    "suggestions": ["Consider adding type hints"],
                    "approved": True,
                    "quality_score": 95
                }
            ]
        ),
        implementation=implementation,
        prompt_template="""
Review the following {language} code:

```{language}
{code}
```

Provide:
1. Critical issues that must be fixed
2. Suggestions for improvement
3. Overall quality score (0-100)
""",
        examples=[
            {
                "input": {"code": "def hello():\n    print('world')", "language": "python"},
                "output": {"issues": [], "suggestions": [], "approved": True, "quality_score": 100}
            }
        ],
        red_flags=[
            "Do not review code without understanding the context",
            "Do not approve code with security vulnerabilities",
            "Do not suggest changes that would break functionality"
        ]
    )


def create_test_generator_skill() -> Skill:
    """创建测试生成skill"""

    def implementation(function_name: str, function_code: str, test_framework: str = "pytest", _project_dir: str = None) -> dict:
        """测试生成实现"""
        if test_framework == "pytest":
            test_code = f"""
import pytest
from mymodule import {function_name}


def test_{function_name}_basic():
    \"\"\"Basic test for {function_name}\"\"\"
    # TODO: Add test implementation
    pass


def test_{function_name}_edge_cases():
    \"\"\"Edge case tests for {function_name}\"\"\"
    # TODO: Add edge case tests
    pass


def test_{function_name}_errors():
    \"\"\"Error handling tests for {function_name}\"\"\"
    # TODO: Add error tests
    pass
"""
        else:
            test_code = f"# Unsupported framework: {test_framework}"

        return {
            "function_name": function_name,
            "test_framework": test_framework,
            "test_code": test_code,
            "num_tests": 3
        }

    return Skill(
        metadata=SkillMetadata(
            name="test-generator",
            version="1.0.0",
            description="Generate unit tests for functions automatically",
            skill_type=SkillType.GENERATION,
            author="Enterprise Team",
            created_at="2025-01-01",
            updated_at="2025-01-01",
            tags=["testing", "code-generation", "quality"]
        ),
        triggers=[
            TriggerRule(
                condition_type=TriggerCondition.KEYWORD,
                pattern="generate tests",
                priority=10
            ),
            TriggerRule(
                condition_type=TriggerCondition.KEYWORD,
                pattern="create test",
                priority=10
            )
        ],
        parameters=[
            SkillParameter(
                name="function_name",
                type="str",
                required=True,
                description="Name of the function to test"
            ),
            SkillParameter(
                name="function_code",
                type="str",
                required=True,
                description="Source code of the function"
            ),
            SkillParameter(
                name="test_framework",
                type="str",
                required=False,
                default="pytest",
                description="Testing framework to use",
                validation=lambda x: x in ["pytest", "unittest", "nose"]
            ),
            SkillParameter(
                name="_project_dir",
                type="str",
                required=False,
                description="Project directory"
            )
        ],
        output=SkillOutput(
            type="dict",
            schema={
                "test_code": "str",
                "num_tests": "int"
            }
        ),
        implementation=implementation,
        examples=[
            {
                "input": {
                    "function_name": "add",
                    "function_code": "def add(a, b): return a + b",
                    "test_framework": "pytest"
                }
            }
        ],
        red_flags=[
            "Do not generate tests without understanding function behavior",
            "Do not skip edge case testing",
            "Do not generate tests that always pass"
        ]
    )


def create_refactor_skill() -> Skill:
    """创建重构skill"""

    def implementation(code: str, refactor_type: str, _project_dir: str = None) -> dict:
        """重构实现"""
        refactored_code = code
        changes = []

        if refactor_type == "extract_function":
            # 简单示例：标记需要提取的部分
            changes.append("Identified code block for extraction")
            refactored_code = f"# TODO: Extract function\n{code}"

        elif refactor_type == "rename_variable":
            changes.append("Suggested variable renames for clarity")

        elif refactor_type == "simplify":
            changes.append("Simplified complex expressions")

        return {
            "original_code": code,
            "refactored_code": refactored_code,
            "refactor_type": refactor_type,
            "changes": changes,
            "improvement_score": 75
        }

    return Skill(
        metadata=SkillMetadata(
            name="refactor",
            version="1.0.0",
            description="Refactor code to improve quality and maintainability",
            skill_type=SkillType.TOOL,
            author="Enterprise Team",
            created_at="2025-01-01",
            updated_at="2025-01-01",
            tags=["refactoring", "code-quality"]
        ),
        triggers=[
            TriggerRule(
                condition_type=TriggerCondition.KEYWORD,
                pattern="refactor",
                priority=10
            )
        ],
        parameters=[
            SkillParameter(
                name="code",
                type="str",
                required=True,
                description="Code to refactor"
            ),
            SkillParameter(
                name="refactor_type",
                type="str",
                required=True,
                description="Type of refactoring",
                validation=lambda x: x in ["extract_function", "rename_variable", "simplify", "remove_duplication"]
            ),
            SkillParameter(
                name="_project_dir",
                type="str",
                required=False
            )
        ],
        output=SkillOutput(
            type="dict",
            schema={
                "refactored_code": "str",
                "changes": "list",
                "improvement_score": "int"
            }
        ),
        implementation=implementation,
        examples=[
            {
                "input": {
                    "code": "def calc(x, y):\n    return x + y",
                    "refactor_type": "rename_variable"
                }
            }
        ],
        red_flags=[
            "Do not refactor without tests",
            "Do not change behavior during refactoring",
            "Do not refactor production code without approval"
        ]
    )


def create_skill_registry_with_examples() -> SkillRegistry:
    """创建包含示例skills的注册表"""
    registry = SkillRegistry()

    # 注册所有示例skills
    registry.register(create_code_review_skill())
    registry.register(create_test_generator_skill())
    registry.register(create_refactor_skill())

    return registry


if __name__ == "__main__":
    # 测试示例skills
    registry = create_skill_registry_with_examples()

    print("Registered Skills:")
    for skill in registry.list_all():
        print(f"  - {skill.metadata.name} v{skill.metadata.version}: {skill.metadata.description}")

    print("\n\nTesting code-review skill:")
    code_review = registry.get("code-review")
    result = code_review.execute(
        code="def hello():\n    print('world')\n    # TODO: add more",
        language="python"
    )
    print(f"Review result: {result}")
