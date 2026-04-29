"""
Agent Base Class - Agent基类
定义所有Agent的通用属性和行为
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import asyncio


class AgentRole(Enum):
    """Agent角色枚举"""
    ARCHITECT = "architect"      # 架构师 - 负责系统设计和规划
    CODER = "coder"              # 程序员 - 负责代码编写
    REVIEWER = "reviewer"        # 评审员 - 负责代码审查
    DEBUGGER = "debugger"        # 调试员 - 负责问题定位和修复
    TESTER = "tester"            # 测试员 - 负责测试用例生成
    ORCHESTRATOR = "orchestrator" # 协调器 - 负责任务分配和协调


class AgentStatus(Enum):
    """Agent状态枚举"""
    IDLE = "idle"                # 空闲
    THINKING = "thinking"        # 思考中
    WORKING = "working"          #工作中
    WAITING = "waiting"          # 等待中
    SUCCESS = "success"          # 成功完成
    FAILED = "failed"            # 失败
    BLOCKED = "blocked"          # 被阻塞


@dataclass
class AgentCapability:
    """Agent能力描述"""
    languages: List[str] = field(default_factory=list)  # 擅长的编程语言
    frameworks: List[str] = field(default_factory=list)  # 擅长的框架
    expertise: List[str] = field(default_factory=list)  # 专业领域
    max_concurrent_tasks: int = 3  # 最大并发任务数


class Agent(ABC):
    """
    Agent基类
    所有专业Agent的父类，提供通用功能和接口
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        role: AgentRole,
        capabilities: Optional[AgentCapability] = None,
        llm_provider: Optional[Callable] = None,
        memory_size: int = 1000
    ):
        self.agent_id = agent_id or str(uuid.uuid4())
        self.name = name
        self.role = role
        self.capabilities = capabilities or AgentCapability()
        self.llm_provider = llm_provider
        self.memory_size = memory_size

        # 状态管理
        self.status = AgentStatus.IDLE
        self.current_task: Optional[str] = None
        self.task_history: List[Dict] = []
        self.long_term_memory: List[Dict] = []

        # 通信相关
        self.inbox: asyncio.Queue = asyncio.Queue()
        self.message_handlers: Dict[str, Callable] = {}
        self.subscribed_events: List[str] = []

        # 指标统计
        self.metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_processing_time": 0.0,
            "messages_sent": 0,
            "messages_received": 0
        }

        # 事件回调
        self.on_status_change: Optional[Callable] = None
        self.on_message_sent: Optional[Callable] = None
        self.on_task_complete: Optional[Callable] = None

    @property
    def unique_id(self) -> str:
        """获取唯一标识"""
        return f"{self.role.value}_{self.agent_id[:8]}"

    @property
    def is_available(self) -> bool:
        """检查Agent是否可用"""
        return self.status == AgentStatus.IDLE and \
               self.metrics["tasks_completed"] < self.capabilities.max_concurrent_tasks

    @abstractmethod
    async def process_task(self, task: Dict) -> Dict:
        """
        处理任务的抽象方法
        子类必须实现具体的任务处理逻辑

        Args:
            task: 任务描述字典

        Returns:
            任务结果字典
        """
        pass

    @abstractmethod
    async def think(self, context: Dict) -> str:
        """
        思考过程的抽象方法
        用于Agent的内部推理和决策

        Args:
            context: 上下文信息

        Returns:
            思考结果
        """
        pass

    async def receive_message(self, message: 'Message') -> None:
        """
        接收消息

        Args:
            message: 消息对象
        """
        self.metrics["messages_received"] += 1
        await self.inbox.put(message)

        # 如果有对应的处理器，触发它
        if message.message_type.value in self.message_handlers:
            handler = self.message_handlers[message.message_type.value]
            await handler(message)

    async def send_message(
        self,
        recipient_id: str,
        content: Any,
        message_type: 'MessageType',
        correlation_id: Optional[str] = None
    ) -> 'Message':
        """
        发送消息

        Args:
            recipient_id: 接收者ID
            content: 消息内容
            message_type: 消息类型
            correlation_id: 关联ID（用于追踪请求-响应）

        Returns:
            发送的消息对象
        """
        message = Message(
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            content=content,
            message_type=message_type,
            correlation_id=correlation_id
        )

        self.metrics["messages_sent"] += 1

        if self.on_message_sent:
            await self.on_message_sent(message)

        return message

    async def broadcast(
        self,
        content: Any,
        message_type: 'MessageType',
        recipients: List[str]
    ) -> List['Message']:
        """
        广播消息给多个接收者

        Args:
            content: 消息内容
            message_type: 消息类型
            recipients: 接收者ID列表

        Returns:
            发送的消息列表
        """
        messages = []
        for recipient_id in recipients:
            msg = await self.send_message(recipient_id, content, message_type)
            messages.append(msg)
        return messages

    def register_handler(self, message_type: str, handler: Callable) -> None:
        """
        注册消息处理器

        Args:
            message_type: 消息类型
            handler: 处理函数
        """
        self.message_handlers[message_type] = handler

    async def update_status(self, new_status: AgentStatus, reason: str = "") -> None:
        """
        更新Agent状态

        Args:
            new_status: 新状态
            reason: 状态变更原因
        """
        old_status = self.status
        self.status = new_status

        if self.on_status_change:
            await self.on_status_change(self, old_status, new_status, reason)

    def add_to_memory(self, key: str, value: Any) -> None:
        """
        添加到长期记忆

        Args:
            key: 记忆键
            value: 记忆值
        """
        self.long_term_memory.append({
            "timestamp": datetime.now().isoformat(),
            "key": key,
            "value": value
        })

        # 限制记忆大小
        if len(self.long_term_memory) > self.memory_size:
            self.long_term_memory = self.long_term_memory[-self.memory_size:]

    def get_from_memory(self, key: str) -> List[Any]:
        """
        从长期记忆获取数据

        Args:
            key: 记忆键

        Returns:
            匹配的记忆列表
        """
        return [
            m["value"] for m in self.long_term_memory
            if m["key"] == key
        ]

    async def execute_with_timeout(
        self,
        coro,
        timeout: float = 30.0
    ) -> Any:
        """
        带超时的执行

        Args:
            coro: 协程
            timeout: 超时时间（秒）

        Returns:
            执行结果

        Raises:
            asyncio.TimeoutError: 执行超时
        """
        try:
            result = await asyncio.wait_for(coro, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            await self.update_status(AgentStatus.FAILED, "Task timeout")
            raise

    def get_capabilities_summary(self) -> Dict:
        """
        获取能力摘要

        Returns:
            能力描述字典
        """
        return {
            "role": self.role.value,
            "languages": self.capabilities.languages,
            "frameworks": self.capabilities.frameworks,
            "expertise": self.capabilities.expertise,
            "max_concurrent": self.capabilities.max_concurrent_tasks
        }

    def get_metrics(self) -> Dict:
        """
        获取Agent指标

        Returns:
            指标字典
        """
        return {
            **self.metrics,
            "current_status": self.status.value,
            "current_task": self.current_task,
            "success_rate": (
                self.metrics["tasks_completed"] /
                max(1, self.metrics["tasks_completed"] + self.metrics["tasks_failed"])
            )
        }

    def to_dict(self) -> Dict:
        """
        序列化为字典

        Returns:
            字典表示
        """
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role.value,
            "status": self.status.value,
            "capabilities": {
                "languages": self.capabilities.languages,
                "frameworks": self.capabilities.frameworks,
                "expertise": self.capabilities.expertise
            },
            "metrics": self.get_metrics()
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.unique_id} status={self.status.value}>"
