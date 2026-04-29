"""
Event Bus - 事件总线
提供发布-订阅模式的事件通信机制
"""

from typing import Dict, List, Callable, Any, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid


class EventType(Enum):
    """事件类型枚举"""
    AGENT_REGISTERED = "agent_registered"
    AGENT_DEREGISTERED = "agent_deregistered"
    AGENT_STATUS_CHANGED = "agent_status_changed"
    TASK_CREATED = "task_created"
    TASK_ASSIGNED = "task_assigned"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    CODE_GENERATED = "code_generated"
    CODE_REVIEWED = "code_reviewed"
    BUG_DETECTED = "bug_detected"
    ERROR_OCCURRED = "error_occurred"
    SYSTEM_SHUTDOWN = "system_shutdown"


@dataclass
class Event:
    """事件类"""
    event_type: EventType
    data: Any
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = ""  # 事件来源

    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source
        }


class EventBus:
    """
    事件总线
    实现发布-订阅模式，支持同步和异步事件处理
    """

    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._wildcard_subscribers: List[Callable] = []  # 订阅所有事件的回调
        self._event_history: List[Event] = []
        self._max_history: int = 1000
        self._lock = asyncio.Lock()

        # 统计信息
        self._stats = {
            "events_published": 0,
            "events_handled": 0,
            "errors": 0
        }

    async def subscribe(self, event_type: EventType, handler: Callable) -> str:
        """
        订阅事件

        Args:
            event_type: 事件类型
            handler: 处理函数

        Returns:
            订阅ID
        """
        async with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []

            subscription_id = str(uuid.uuid4())
            self._subscribers[event_type].append(handler)

            return subscription_id

    async def unsubscribe(self, event_type: EventType, handler: Callable) -> None:
        """
        取消订阅

        Args:
            event_type: 事件类型
            handler: 处理函数
        """
        async with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(handler)
                except ValueError:
                    pass

    async def subscribe_wildcard(self, handler: Callable) -> str:
        """
        订阅所有事件

        Args:
            handler: 处理函数

        Returns:
            订阅ID
        """
        async with self._lock:
            subscription_id = str(uuid.uuid4())
            self._wildcard_subscribers.append(handler)
            return subscription_id

    async def publish(self, event: Event) -> None:
        """
        发布事件

        Args:
            event: 事件对象
        """
        async with self._lock:
            self._stats["events_published"] += 1

            # 添加到历史
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history = self._event_history[-self._max_history:]

        # 获取所有需要通知的处理器
        handlers = []
        async with self._lock:
            if event.event_type in self._subscribers:
                handlers.extend(self._subscribers[event.event_type])
            handlers.extend(self._wildcard_subscribers)

        # 异步执行所有处理器
        tasks = []
        for handler in handlers:
            task = asyncio.create_task(self._safe_handle(handler, event))
            tasks.append(task)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_handle(self, handler: Callable, event: Event) -> None:
        """安全地执行事件处理"""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
            self._stats["events_handled"] += 1
        except Exception as e:
            self._stats["errors"] += 1
            # 发布错误事件
            await self.publish(Event(
                event_type=EventType.ERROR_OCCURRED,
                data={"error": str(e), "original_event": event.to_dict()},
                source="event_bus"
            ))

    async def publish_async(self, event_type: EventType, data: Any, source: str = "") -> None:
        """
        异步发布事件的便捷方法

        Args:
            event_type: 事件类型
            data: 事件数据
            source: 事件来源
        """
        await self.publish(Event(
            event_type=event_type,
            data=data,
            source=source
        ))

    def get_history(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        获取事件历史

        Args:
            event_type: 过滤的事件类型
            limit: 返回数量限制

        Returns:
            事件列表
        """
        if event_type:
            filtered = [e for e in self._event_history if e.event_type == event_type]
            return filtered[-limit:]
        return self._event_history[-limit:]

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self._stats,
            "subscriber_count": sum(len(h) for h in self._subscribers.values()),
            "wildcard_count": len(self._wildcard_subscribers),
            "history_size": len(self._event_history)
        }

    def clear_history(self) -> None:
        """清空事件历史"""
        self._event_history.clear()
