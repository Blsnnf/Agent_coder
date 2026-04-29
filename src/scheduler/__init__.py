"""
Task Scheduler - 任务调度器
负责任务的创建、分配、跟踪和协调
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Callable
from datetime import datetime
from collections import defaultdict
import asyncio
import uuid
import json


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"           # 待处理
    QUEUED = "queued"            # 已入队
    ASSIGNED = "assigned"         # 已分配
    IN_PROGRESS = "in_progress"  # 进行中
    WAITING_DEPENDENCIES = "waiting_dependencies"  # 等待依赖
    BLOCKED = "blocked"          # 被阻塞
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"      # 已取消


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Task:
    """任务类"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    task_type: str = "general"  # general, code, review, debug, design
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    assigned_agent: Optional[str] = None

    # 依赖关系
    dependencies: List[str] = field(default_factory=list)  # 依赖的任务ID
    dependents: List[str] = field(default_factory=list)   # 依赖此任务的任务

    # 输入输出
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Optional[Any] = None

    # 时间和统计
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration: int = 300  # 预估时长（秒）

    # 上下文
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 追踪
    events: List[Dict] = field(default_factory=list)
    error: Optional[str] = None

    def add_event(self, event_type: str, details: Optional[Dict] = None) -> None:
        """添加事件记录"""
        self.events.append({
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "details": details or {}
        })

    def can_execute(self, completed_tasks: Set[str]) -> bool:
        """检查任务是否可以执行"""
        if self.status not in [TaskStatus.PENDING, TaskStatus.QUEUED]:
            return False
        return all(dep in completed_tasks for dep in self.dependencies)

    def get_duration(self) -> float:
        """获取任务执行时长"""
        if self.started_at:
            end = self.completed_at or datetime.now()
            return (end - self.started_at).total_seconds()
        return 0.0

    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "task_type": self.task_type,
            "status": self.status.value,
            "priority": self.priority.value,
            "assigned_agent": self.assigned_agent,
            "dependencies": self.dependencies,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration": self.get_duration(),
            "error": self.error
        }


class TaskScheduler:
    """
    任务调度器
    管理任务的创建、分配、执行和完成
    """

    def __init__(self, event_bus: Optional['EventBus'] = None):
        self.event_bus = event_bus

        # 任务存储
        self.tasks: Dict[str, Task] = {}
        self.tasks_by_status: Dict[TaskStatus, List[str]] = defaultdict(list)
        self.tasks_by_agent: Dict[str, List[str]] = defaultdict(list)

        # 队列
        self.pending_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.priority_queue: Dict[TaskPriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in TaskPriority
        }

        # Agent管理
        self.agents: Dict[str, 'Agent'] = {}
        self.agent_availability: Dict[str, bool] = {}

        # 回调
        self.on_task_assigned: Optional[Callable] = None
        self.on_task_completed: Optional[Callable] = None

        # 统计
        self.stats = {
            "tasks_created": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "avg_duration": 0.0
        }

        # 运行状态
        self._running = False
        self._dispatcher_task: Optional[asyncio.Task] = None

    def register_agent(self, agent: 'Agent') -> None:
        """
        注册Agent

        Args:
            agent: Agent实例
        """
        self.agents[agent.agent_id] = agent
        self.agent_availability[agent.agent_id] = True
        agent.on_status_change = self._handle_agent_status_change

    def unregister_agent(self, agent_id: str) -> None:
        """注销Agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            del self.agent_availability[agent_id]

    async def _handle_agent_status_change(
        self,
        agent: 'Agent',
        old_status: 'AgentStatus',
        new_status: 'AgentStatus',
        reason: str
    ) -> None:
        """处理Agent状态变更"""
        self.agent_availability[agent.agent_id] = (new_status == 'AgentStatus.IDLE')

        if new_status == 'AgentStatus.IDLE' and self._running:
            await self._dispatch_task(agent.agent_id)

    async def create_task(
        self,
        title: str,
        description: str,
        task_type: str = "general",
        priority: TaskPriority = TaskPriority.NORMAL,
        dependencies: Optional[List[str]] = None,
        input_data: Optional[Dict] = None,
        context: Optional[Dict] = None
    ) -> Task:
        """
        创建任务

        Args:
            title: 任务标题
            description: 任务描述
            task_type: 任务类型
            priority: 优先级
            dependencies: 依赖任务ID列表
            input_data: 输入数据
            context: 上下文

        Returns:
            创建的任务对象
        """
        task = Task(
            title=title,
            description=description,
            task_type=task_type,
            priority=priority,
            dependencies=dependencies or [],
            input_data=input_data or {},
            context=context or {}
        )

        self.tasks[task.task_id] = task
        self.tasks_by_status[TaskStatus.PENDING].append(task.task_id)
        task.add_event("created")

        self.stats["tasks_created"] += 1

        # 发布事件
        if self.event_bus:
            await self.event_bus.publish_async(
                'EventType.TASK_CREATED',
                task.to_dict(),
                source="scheduler"
            )

        # 如果可以执行，加入调度队列
        await self._queue_task(task)

        return task

    async def _queue_task(self, task: Task) -> None:
        """将任务加入调度队列"""
        if task.can_execute(set()):
            await self.pending_queue.put((3 - task.priority.value, task.task_id))
            task.status = TaskStatus.QUEUED
            self.tasks_by_status[TaskStatus.QUEUED].append(task.task_id)
            self.tasks_by_status[TaskStatus.PENDING].remove(task.task_id)

    async def assign_task(self, task_id: str, agent_id: str) -> bool:
        """
        分配任务给Agent

        Args:
            task_id: 任务ID
            agent_id: Agent ID

        Returns:
            是否分配成功
        """
        if task_id not in self.tasks or agent_id not in self.agents:
            return False

        task = self.tasks[task_id]
        agent = self.agents[agent_id]

        if not agent.is_available:
            return False

        task.assigned_agent = agent_id
        task.status = TaskStatus.ASSIGNED
        task.add_event("assigned", {"agent_id": agent_id})

        self.tasks_by_status[TaskStatus.ASSIGNED].append(task_id)
        if task_id in self.tasks_by_status[TaskStatus.QUEUED]:
            self.tasks_by_status[TaskStatus.QUEUED].remove(task_id)

        self.tasks_by_agent[agent_id].append(task_id)

        if self.on_task_assigned:
            await self.on_task_assigned(task, agent)

        if self.event_bus:
            await self.event_bus.publish_async(
                'EventType.TASK_ASSIGNED',
                {"task_id": task_id, "agent_id": agent_id},
                source="scheduler"
            )

        return True

    async def _dispatch_task(self, agent_id: str) -> None:
        """为Agent分配任务"""
        if agent_id not in self.agents:
            return

        # 查找该Agent擅长处理的任务类型
        agent = self.agents[agent_id]
        preferred_types = agent.capabilities.languages + agent.capabilities.frameworks

        # 从队列中获取任务
        try:
            priority, task_id = await asyncio.wait_for(
                self.pending_queue.get(),
                timeout=1.0
            )
        except asyncio.TimeoutError:
            return

        task = self.tasks.get(task_id)
        if not task:
            return

        # 尝试分配任务
        if await self.assign_task(task_id, agent_id):
            # 启动任务执行
            asyncio.create_task(self._execute_task(task_id))
        else:
            # 重新放回队列
            await self.pending_queue.put((priority, task_id))

    async def _execute_task(self, task_id: str) -> None:
        """执行任务"""
        task = self.tasks.get(task_id)
        if not task:
            return

        agent = self.agents.get(task.assigned_agent)
        if not agent:
            task.status = TaskStatus.FAILED
            task.error = "No agent assigned"
            return

        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()
        task.add_event("started")

        if self.event_bus:
            await self.event_bus.publish_async(
                'EventType.TASK_PROGRESS',
                {"task_id": task_id, "status": "started"},
                source="scheduler"
            )

        try:
            # 调用Agent处理任务
            result = await agent.process_task({
                "task_id": task_id,
                "title": task.title,
                "description": task.description,
                "input_data": task.input_data,
                "context": task.context
            })

            task.output_data = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.add_event("completed", {"result": result})

            self.stats["tasks_completed"] += 1

            if self.event_bus:
                await self.event_bus.publish_async(
                    'EventType.TASK_COMPLETED',
                    task.to_dict(),
                    source="scheduler"
                )

            # 触发依赖此任务的其他任务
            await self._check_dependents(task_id)

            if self.on_task_completed:
                await self.on_task_completed(task, agent)

            # 更新Agent状态
            await agent.update_status('AgentStatus.IDLE', "Task completed")

            # 尝试分配下一个任务
            await self._dispatch_task(task.assigned_agent)

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            task.add_event("failed", {"error": str(e)})

            self.stats["tasks_failed"] += 1

            if self.event_bus:
                await self.event_bus.publish_async(
                    'EventType.TASK_FAILED',
                    task.to_dict(),
                    source="scheduler"
                )

    async def _check_dependents(self, completed_task_id: str) -> None:
        """检查并触发依赖任务"""
        completed_task = self.tasks.get(completed_task_id)
        if not completed_task:
            return

        for dependent_id in completed_task.dependents:
            dependent = self.tasks.get(dependent_id)
            if dependent and dependent.can_execute(
                {t.task_id for t in self.tasks.values() if t.status == TaskStatus.COMPLETED}
            ):
                await self._queue_task(dependent)

    async def start(self) -> None:
        """启动调度器"""
        self._running = True
        self._dispatcher_task = asyncio.create_task(self._dispatch_loop())

    async def stop(self) -> None:
        """停止调度器"""
        self._running = False
        if self._dispatcher_task:
            self._dispatcher_task.cancel()
            try:
                await self._dispatcher_task
            except asyncio.CancelledError:
                pass

    async def _dispatch_loop(self) -> None:
        """任务分发循环"""
        while self._running:
            try:
                # 检查可用的Agent
                available_agents = [
                    agent_id for agent_id, available in self.agent_availability.items()
                    if available
                ]

                # 为每个可用Agent分配任务
                for agent_id in available_agents:
                    await self._dispatch_task(agent_id)

                await asyncio.sleep(0.5)

            except Exception as e:
                if self.event_bus:
                    await self.event_bus.publish_async(
                        'EventType.ERROR_OCCURRED',
                        {"error": str(e), "source": "dispatcher"},
                        source="scheduler"
                    )

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        task = self.tasks.get(task_id)
        if task:
            return task.to_dict()
        return None

    def get_agent_tasks(self, agent_id: str) -> List[Dict]:
        """获取Agent的任务列表"""
        return [
            self.tasks[task_id].to_dict()
            for task_id in self.tasks_by_agent.get(agent_id, [])
            if task_id in self.tasks
        ]

    def get_stats(self) -> Dict:
        """获取调度器统计"""
        return {
            **self.stats,
            "total_tasks": len(self.tasks),
            "pending_tasks": len(self.tasks_by_status[TaskStatus.PENDING]),
            "queued_tasks": len(self.tasks_by_status[TaskStatus.QUEUED]),
            "in_progress_tasks": len(self.tasks_by_status[TaskStatus.IN_PROGRESS]),
            "completed_tasks": len(self.tasks_by_status[TaskStatus.COMPLETED]),
            "failed_tasks": len(self.tasks_by_status[TaskStatus.FAILED]),
            "active_agents": sum(1 for a in self.agents.values() if a.status == 'AgentStatus.WORKING')
        }
