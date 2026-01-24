"""
Skill Definition Schema
定义企业级Agent Skill的数据结构
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from enum import Enum


class SkillType(Enum):
    """Skill类型"""
    TOOL = "tool"
    WORKFLOW = "workflow"
    ANALYSIS = "analysis"
    GENERATION = "generation"


class TriggerCondition(Enum):
    """触发条件类型"""
    KEYWORD = "keyword"
    CONTEXT = "context"
    EXPLICIT = "explicit"
    AUTO = "auto"


@dataclass
class SkillMetadata:
    """Skill元数据"""
    name: str
    version: str
    description: str
    skill_type: SkillType
    author: str
    created_at: str
    updated_at: str
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class TriggerRule:
    """触发规则"""
    condition_type: TriggerCondition
    pattern: str  # 关键词、正则或上下文描述
    priority: int = 0
    context_requirements: Dict[str, any] = field(default_factory=dict)

    def matches(self, input_text: str, context: Dict = None) -> bool:
        """检查是否匹配触发条件"""
        if self.condition_type == TriggerCondition.KEYWORD:
            return self.pattern.lower() in input_text.lower()
        elif self.condition_type == TriggerCondition.EXPLICIT:
            return self.pattern == input_text
        elif self.condition_type == TriggerCondition.CONTEXT:
            if context is None:
                return False
            return all(
                context.get(k) == v
                for k, v in self.context_requirements.items()
            )
        return False


@dataclass
class SkillParameter:
    """Skill参数定义"""
    name: str
    type: str
    required: bool = True
    default: any = None
    description: str = ""
    validation: Optional[Callable] = None


@dataclass
class SkillOutput:
    """Skill输出定义"""
    type: str
    schema: Dict = field(default_factory=dict)
    examples: List[any] = field(default_factory=list)


@dataclass
class Skill:
    """完整的Skill定义"""
    metadata: SkillMetadata
    triggers: List[TriggerRule]
    parameters: List[SkillParameter]
    output: SkillOutput
    implementation: Optional[Callable] = None
    prompt_template: str = ""
    examples: List[Dict] = field(default_factory=list)
    red_flags: List[str] = field(default_factory=list)

    def validate(self) -> List[str]:
        """验证skill定义的完整性"""
        errors = []

        # 验证metadata
        if not self.metadata.name:
            errors.append("Skill name is required")
        if not self.metadata.version:
            errors.append("Skill version is required")
        if not self.metadata.description:
            errors.append("Skill description is required")

        # 验证triggers
        if not self.triggers:
            errors.append("At least one trigger rule is required")

        # 验证parameters
        required_params = [p for p in self.parameters if p.required]
        for param in required_params:
            if param.default is not None:
                errors.append(f"Required parameter '{param.name}' cannot have default value")

        # 验证implementation或prompt_template存在
        if not self.implementation and not self.prompt_template:
            errors.append("Either implementation or prompt_template is required")

        return errors

    def can_trigger(self, input_text: str, context: Dict = None) -> bool:
        """检查是否可以触发此skill"""
        return any(trigger.matches(input_text, context) for trigger in self.triggers)

    def execute(self, **kwargs) -> any:
        """执行skill"""
        # 验证参数
        param_errors = self._validate_parameters(kwargs)
        if param_errors:
            raise ValueError(f"Parameter validation failed: {param_errors}")

        # 执行implementation
        if self.implementation:
            return self.implementation(**kwargs)
        else:
            raise NotImplementedError("Skill implementation not provided")

    def _validate_parameters(self, params: Dict) -> List[str]:
        """验证执行参数"""
        errors = []

        # 检查必需参数
        required_param_names = {p.name for p in self.parameters if p.required}
        provided_params = set(params.keys())
        missing_params = required_param_names - provided_params

        if missing_params:
            errors.append(f"Missing required parameters: {missing_params}")

        # 检查参数类型和验证
        for param in self.parameters:
            if param.name in params:
                value = params[param.name]
                # 自定义验证
                if param.validation and not param.validation(value):
                    errors.append(f"Validation failed for parameter '{param.name}'")

        return errors


@dataclass
class SkillRegistry:
    """Skill注册表"""
    skills: Dict[str, Skill] = field(default_factory=dict)

    def register(self, skill: Skill) -> None:
        """注册skill"""
        # 验证skill
        errors = skill.validate()
        if errors:
            raise ValueError(f"Skill validation failed: {errors}")

        skill_id = f"{skill.metadata.name}@{skill.metadata.version}"
        self.skills[skill_id] = skill

    def get(self, name: str, version: str = None) -> Optional[Skill]:
        """获取skill"""
        if version:
            skill_id = f"{name}@{version}"
            return self.skills.get(skill_id)
        else:
            # 返回最新版本
            matching_skills = [
                s for s in self.skills.values()
                if s.metadata.name == name
            ]
            if matching_skills:
                return max(matching_skills, key=lambda s: s.metadata.version)
        return None

    def find_by_trigger(self, input_text: str, context: Dict = None) -> List[Skill]:
        """根据触发条件查找skills"""
        return [
            skill for skill in self.skills.values()
            if skill.can_trigger(input_text, context)
        ]

    def list_all(self) -> List[Skill]:
        """列出所有skills"""
        return list(self.skills.values())
