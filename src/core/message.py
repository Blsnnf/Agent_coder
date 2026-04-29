"""
Message System - 消息系统
定义Agent间通信的消息格式和类型
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List
from datetime import datetime
import uuid


class MessageType(Enum):
    """消息类型枚举"""
    # 任务相关
    TASK_REQUEST = "task_request"       # 任务请求
    TASK_RESPONSE = "task_response"     # 任务响应
    TASK_PROGRESS = "task_progress"     # 任务进度
    TASK_COMPLETE = "task_complete"    # 任务完成
    TASK_CANCEL = "task_cancel"          # 任务取消
    TASK_ERROR = "task_error"           # 任务错误

    # 协作相关
    HELP_REQUEST = "help_request"       # 请求帮助
    HELP_RESPONSE = "help_response"     # 帮助响应
    COLLABORATION = "collaboration"     # 协作消息
    CONSENSUS = "consensus"             # 共识请求

    # 代码相关
    CODE_REVIEW = "code_review"         # 代码审查请求
    CODE_SUGGESTION = "code_suggestion" # 代码建议
    BUG_REPORT = "bug_report"           # Bug报告
    FIX_APPLIED = "fix_applied"         # 修复应用

    # 系统相关
    HEARTBEAT = "heartbeat"             # 心跳
    STATUS_UPDATE = "status_update"    # 状态更新
    REGISTRATION = "registration"       # 注册
    DEREGISTRATION = "deregistration"   # 注销


@dataclass
class Message:
    """
    消息类
    Agent间通信的基本单位
    """
    sender_id: str                                    # 发送者ID
    recipient_id: str                                 # 接收者ID
    content: Any                                      # 消息内容
    message_type: MessageType                         # 消息类型

    # 元数据
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None              # 关联ID（用于请求-响应匹配）
    timestamp: datetime = field(default_factory=datetime.now)
    reply_to: Optional[str] = None                    # 回复地址
    ttl: int = 3600                                   # 生存时间（秒）
    priority: int = 0                                 # 优先级（0-9，9最高）

    # 附件和上下文
    attachments: List[Any] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 追踪信息
    trace: List[Dict] = field(default_factory=list)

    def add_trace_entry(self, agent_id: str, action: str, details: Optional[Dict] = None) -> None:
        """
        添加追踪条目

        Args:
            agent_id: Agent ID
            action: 操作描述
            details: 详细信息
        """
        self.trace.append({
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "action": action,
            "details": details or {}
        })

    def is_expired(self) -> bool:
        """
        检查消息是否过期

        Returns:
            是否过期
        """
        age = (datetime.now() - self.timestamp).total_seconds()
        return age > self.ttl

    def create_reply(self, content: Any, message_type: MessageType) -> 'Message':
        """
        创建回复消息

        Args:
            content: 回复内容
            message_type: 回复消息类型

        Returns:
            回复消息
        """
        return Message(
            sender_id=self.recipient_id,
            recipient_id=self.sender_id,
            content=content,
            message_type=message_type,
            correlation_id=self.message_id,
            reply_to=self.reply_to,
            context=self.context.copy()
        )

    def to_dict(self) -> Dict:
        """
        序列化为字典

        Returns:
            字典表示
        """
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "content": self.content,
            "message_type": self.message_type.value,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority,
            "trace": self.trace
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        """
        从字典创建消息

        Args:
            data: 字典数据

        Returns:
            消息对象
        """
        return cls(
            message_id=data.get("message_id", str(uuid.uuid4())),
            sender_id=data["sender_id"],
            recipient_id=data["recipient_id"],
            content=data["content"],
            message_type=MessageType(data["message_type"]),
            correlation_id=data.get("correlation_id"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if isinstance(data.get("timestamp"), str) else datetime.now(),
            priority=data.get("priority", 0),
            trace=data.get("trace", [])
        )

    def __repr__(self) -> str:
        return f"<Message id={self.message_id[:8]} type={self.message_type.value} from={self.sender_id[:8]} to={self.recipient_id[:8]}>"


class MessageBuilder:
    """
    消息构建器
    提供便捷的消息创建方法
    """

    @staticmethod
    def task_request(
        sender_id: str,
        recipient_id: str,
        task: Dict,
        correlation_id: Optional[str] = None
    ) -> Message:
        """创建任务请求消息"""
        return Message(
            sender_id=sender_id,
            recipient_id=recipient_id,
            content={"task": task},
            message_type=MessageType.TASK_REQUEST,
            correlation_id=correlation_id
        )

    @staticmethod
    def task_response(
        sender_id: str,
        recipient_id: str,
        result: Any,
        correlation_id: str
    ) -> Message:
        """创建任务响应消息"""
        return Message(
            sender_id=sender_id,
            recipient_id=recipient_id,
            content={"result": result},
            message_type=MessageType.TASK_RESPONSE,
            correlation_id=correlation_id
        )

    @staticmethod
    def code_review_request(
        sender_id: str,
        recipient_id: str,
        code: str,
        language: str,
        context: Optional[Dict] = None
    ) -> Message:
        """创建代码审查请求"""
        return Message(
            sender_id=sender_id,
            recipient_id=recipient_id,
            content={
                "code": code,
                "language": language,
                "context": context or {}
            },
            message_type=MessageType.CODE_REVIEW
        )

    @staticmethod
    def help_request(
        sender_id: str,
        recipient_ids: List[str],
        problem: str,
        context: Dict
    ) -> List[Message]:
        """创建帮助请求（可发送给多个Agent）"""
        return [
            Message(
                sender_id=sender_id,
                recipient_id=recipient_id,
                content={"problem": problem, "context": context},
                message_type=MessageType.HELP_REQUEST
            )
            for recipient_id in recipient_ids
        ]
