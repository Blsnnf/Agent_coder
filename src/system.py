"""
Multi-Agent Coding System - Main System
多智能体协同自动编程系统 - 主系统
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import uuid

from .core.agent import Agent, AgentRole, AgentStatus, AgentCapability
from .core.message import Message, MessageType
from .core.event_bus import EventBus, EventType
from .scheduler.task_scheduler import TaskScheduler, TaskPriority
from .executor.code_executor import CodeExecutor
from .agents.architect_agent import ArchitectAgent
from .agents.coder_agent import CoderAgent
from .agents.reviewer_agent import ReviewerAgent
from .agents.debugger_agent import DebuggerAgent


class Orchestrator:
    """
    协调器
    负责协调多个Agent的工作，实现任务协作
    """

    def __init__(self):
        self.agent_id = str(uuid.uuid4())
        self.name = "System Orchestrator"
        self.task_scheduler: Optional[TaskScheduler] = None
        self.event_bus: Optional[EventBus] = None
        self.code_executor: Optional[CodeExecutor] = None

        # Agent注册表
        self.agents: Dict[str, Agent] = {}
        self.agent_roles: Dict[AgentRole, List[Agent]] = {}

        # 协作工作流
        self.workflows: Dict[str, Callable] = {
            "code_development": self._code_development_workflow,
            "bug_fix": self._bug_fix_workflow,
            "code_review": self._code_review_workflow,
            "architecture_design": self._architecture_design_workflow
        }

    def register_agent(self, agent: Agent) -> None:
        """注册Agent"""
        self.agents[agent.agent_id] = agent

        if agent.role not in self.agent_roles:
            self.agent_roles[agent.role] = []
        self.agent_roles[agent.role].append(agent)

        print(f"Registered agent: {agent.name} ({agent.role.value})")

    def get_agent_by_role(self, role: AgentRole) -> Optional[Agent]:
        """根据角色获取Agent"""
        agents = self.agent_roles.get(role, [])
        for agent in agents:
            if agent.is_available:
                return agent
        return agents[0] if agents else None

    async def initialize(
        self,
        event_bus: EventBus,
        code_executor: CodeExecutor,
        llm_provider: Optional[Callable] = None
    ) -> None:
        """
        初始化系统

        Args:
            event_bus: 事件总线
            code_executor: 代码执行器
            llm_provider: LLM提供者（可选）
        """
        self.event_bus = event_bus
        self.code_executor = code_executor

        # 创建任务调度器
        self.task_scheduler = TaskScheduler(event_bus)

        # 注册所有专业Agent
        self._register_default_agents(llm_provider)

        # 将Agent注册到调度器
        for agent in self.agents.values():
            self.task_scheduler.register_agent(agent)

        # 启动调度器
        await self.task_scheduler.start()

        print("System initialized successfully")

    def _register_default_agents(self, llm_provider: Optional[Callable] = None) -> None:
        """注册默认Agent"""
        # 架构师
        self.register_agent(ArchitectAgent(
            agent_id="architect_1",
            name="Alice - Architect",
            llm_provider=llm_provider
        ))

        # 程序员
        self.register_agent(CoderAgent(
            agent_id="coder_1",
            name="Bob - Coder",
            llm_provider=llm_provider,
            executor=self.code_executor
        ))
        self.register_agent(CoderAgent(
            agent_id="coder_2",
            name="Charlie - Coder",
            llm_provider=llm_provider,
            executor=self.code_executor
        ))

        # 评审员
        self.register_agent(ReviewerAgent(
            agent_id="reviewer_1",
            name="Diana - Reviewer",
            llm_provider=llm_provider
        ))

        # 调试员
        self.register_agent(DebuggerAgent(
            agent_id="debugger_1",
            name="Eve - Debugger",
            llm_provider=llm_provider
        ))

    async def create_task(
        self,
        title: str,
        description: str,
        workflow: Optional[str] = None,
        task_type: str = "general",
        priority: TaskPriority = TaskPriority.NORMAL,
        input_data: Optional[Dict] = None
    ) -> str:
        """
        创建任务

        Args:
            title: 任务标题
            description: 任务描述
            workflow: 工作流类型
            task_type: 任务类型
            priority: 优先级
            input_data: 输入数据

        Returns:
            任务ID
        """
        task = await self.task_scheduler.create_task(
            title=title,
            description=description,
            task_type=task_type,
            priority=priority,
            input_data=input_data
        )

        print(f"Task created: {task.task_id} - {title}")

        # 如果指定了工作流，执行工作流
        if workflow and workflow in self.workflows:
            asyncio.create_task(self.workflows[workflow](task.task_id))

        return task.task_id

    async def _code_development_workflow(self, task_id: str) -> None:
        """代码开发工作流：设计 -> 编码 -> 审查 -> 修复"""
        print(f"Starting code development workflow for task: {task_id}")

        # 1. 获取架构师设计
        architect = self.get_agent_by_role(AgentRole.ARCHITECT)
        if architect:
            design_task = await self.task_scheduler.create_task(
                title=f"Design for {task_id}",
                description="Design system architecture",
                task_type="design"
            )
            # 等待设计完成
            await asyncio.sleep(2)

        # 2. 分配给程序员编码
        coder = self.get_agent_by_role(AgentRole.CODER)
        if coder:
            print(f"Assigned coding to {coder.name}")

        # 3. 分配给评审员审查
        reviewer = self.get_agent_by_role(AgentRole.REVIEWER)
        if reviewer:
            print(f"Assigned review to {reviewer.name}")

    async def _bug_fix_workflow(self, task_id: str) -> None:
        """Bug修复工作流：定位 -> 分析 -> 修复 -> 验证"""
        print(f"Starting bug fix workflow for task: {task_id}")

        debugger = self.get_agent_by_role(AgentRole.DEBUGGER)
        if debugger:
            print(f"Assigned debugging to {debugger.name}")

    async def _code_review_workflow(self, task_id: str) -> None:
        """代码审查工作流"""
        print(f"Starting code review workflow for task: {task_id}")

        reviewer = self.get_agent_by_role(AgentRole.REVIEWER)
        if reviewer:
            print(f"Assigned review to {reviewer.name}")

    async def _architecture_design_workflow(self, task_id: str) -> None:
        """架构设计工作流"""
        print(f"Starting architecture design workflow for task: {task_id}")

        architect = self.get_agent_by_role(AgentRole.ARCHITECT)
        if architect:
            print(f"Assigned architecture design to {architect.name}")

    async def shutdown(self) -> None:
        """关闭系统"""
        if self.task_scheduler:
            await self.task_scheduler.stop()
        print("System shutdown complete")

    def get_system_status(self) -> Dict:
        """获取系统状态"""
        return {
            "initialized": self.task_scheduler is not None,
            "agent_count": len(self.agents),
            "agents_by_role": {
                role.value: len(agents)
                for role, agents in self.agent_roles.items()
            },
            "scheduler": self.task_scheduler.get_stats() if self.task_scheduler else {},
            "executor": self.code_executor.get_stats() if self.code_executor else {}
        }


class MultiAgentCodingSystem:
    """
    多智能体协同自动编程系统
    主入口类
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.orchestrator: Optional[Orchestrator] = None
        self.event_bus: Optional[EventBus] = None
        self.code_executor: Optional[CodeExecutor] = None
        self._running = False

    async def initialize(self, llm_provider: Optional[Callable] = None) -> None:
        """初始化系统"""
        # 创建事件总线
        self.event_bus = EventBus()

        # 创建代码执行器
        self.code_executor = CodeExecutor()

        # 创建协调器
        self.orchestrator = Orchestrator()
        await self.orchestrator.initialize(
            event_bus=self.event_bus,
            code_executor=self.code_executor,
            llm_provider=llm_provider
        )

        self._running = True
        print("=" * 60)
        print("Multi-Agent Collaborative Auto-Programming System")
        print("=" * 60)
        print(f"Agents registered: {len(self.orchestrator.agents)}")
        print("Status: Ready")
        print("=" * 60)

    async def create_code_task(
        self,
        requirement: str,
        language: str = "python",
        framework: Optional[str] = None,
        priority: int = 1
    ) -> str:
        """
        创建代码开发任务

        Args:
            requirement: 需求描述
            language: 目标语言
            framework: 框架
            priority: 优先级

        Returns:
            任务ID
        """
        task_id = await self.orchestrator.create_task(
            title=f"Implement: {requirement[:50]}",
            description=requirement,
            workflow="code_development",
            task_type="code",
            priority=TaskPriority(priority),
            input_data={
                "requirement": requirement,
                "language": language,
                "framework": framework
            }
        )
        return task_id

    async def create_review_task(
        self,
        code: str,
        language: str = "python"
    ) -> str:
        """创建代码审查任务"""
        task_id = await self.orchestrator.create_task(
            title="Code Review",
            description="Review code for quality and issues",
            workflow="code_review",
            task_type="review",
            input_data={
                "code": code,
                "language": language
            }
        )
        return task_id

    async def create_debug_task(
        self,
        error: str,
        code: Optional[str] = None,
        stack_trace: Optional[str] = None,
        language: str = "python"
    ) -> str:
        """创建调试任务"""
        task_id = await self.orchestrator.create_task(
            title="Debug Task",
            description=f"Debug error: {error[:50]}",
            workflow="bug_fix",
            task_type="debug",
            input_data={
                "error": error,
                "code": code,
                "stack_trace": stack_trace,
                "language": language
            }
        )
        return task_id

    async def execute_code(
        self,
        code: str,
        language: str,
        stdin: Optional[str] = None
    ) -> Dict:
        """
        执行代码

        Args:
            code: 代码
            language: 语言
            stdin: 标准输入

        Returns:
            执行结果
        """
        from .executor.code_executor import CodeLanguage

        lang_map = {
            "python": CodeLanguage.PYTHON,
            "javascript": CodeLanguage.JAVASCRIPT,
            "typescript": CodeLanguage.TYPESCRIPT,
            "java": CodeLanguage.JAVA,
            "go": CodeLanguage.GO,
            "rust": CodeLanguage.RUST,
            "c": CodeLanguage.C,
            "cpp": CodeLanguage.CPP,
            "bash": CodeLanguage.BASH
        }

        lang = lang_map.get(language.lower(), CodeLanguage.PYTHON)
        result = await self.code_executor.execute(code, lang, stdin)

        return result.to_dict()

    def get_status(self) -> Dict:
        """获取系统状态"""
        return self.orchestrator.get_system_status() if self.orchestrator else {}

    async def shutdown(self) -> None:
        """关闭系统"""
        if self.orchestrator:
            await self.orchestrator.shutdown()
        self._running = False


# 便捷函数
async def create_system(config: Optional[Dict] = None) -> MultiAgentCodingSystem:
    """创建并初始化系统"""
    system = MultiAgentCodingSystem(config)
    await system.initialize()
    return system
