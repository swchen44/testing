"""
Enterprise Agent Skill Testing Framework

一个系统化、企业级的Agent Skill测试框架
支持单元测试、集成测试、端到端测试和回归检测

主要模块:
- skill_schema: Skill定义和数据结构
- unit_test_framework: 单元测试框架
- integration_test_framework: 集成测试框架
- e2e_test_framework: 端到端测试框架
- test_runner: 统一测试运行器
- example_skills: 示例skills
"""

__version__ = "1.0.0"
__author__ = "Enterprise Team"

from .skill_schema import (
    Skill,
    SkillMetadata,
    SkillType,
    TriggerRule,
    TriggerCondition,
    SkillParameter,
    SkillOutput,
    SkillRegistry
)

from .unit_test_framework import (
    SkillUnitTester,
    TriggerTestSuite,
    TestResult,
    TestStatus
)

from .integration_test_framework import (
    SkillIntegrationTester,
    IntegrationTestCase,
    PerformanceTester
)

from .e2e_test_framework import (
    E2ETestRunner,
    E2ETestCase,
    WorkflowStep,
    RegressionDetector
)

from .test_runner import (
    UnifiedTestRunner,
    ContinuousTestingPipeline
)

__all__ = [
    # Schema
    'Skill',
    'SkillMetadata',
    'SkillType',
    'TriggerRule',
    'TriggerCondition',
    'SkillParameter',
    'SkillOutput',
    'SkillRegistry',

    # Unit Testing
    'SkillUnitTester',
    'TriggerTestSuite',
    'TestResult',
    'TestStatus',

    # Integration Testing
    'SkillIntegrationTester',
    'IntegrationTestCase',
    'PerformanceTester',

    # E2E Testing
    'E2ETestRunner',
    'E2ETestCase',
    'WorkflowStep',
    'RegressionDetector',

    # Test Runner
    'UnifiedTestRunner',
    'ContinuousTestingPipeline',
]
