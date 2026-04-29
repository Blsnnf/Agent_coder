"""
Test Suite for Multi-Agent Coding System
测试套件
"""

import pytest
import asyncio
from src.core.agent import Agent, AgentRole, AgentStatus, AgentCapability
from src.core.message import Message, MessageType
from src.core.event_bus import EventBus, EventType
from src.scheduler.task_scheduler import TaskScheduler, TaskPriority
from src.executor.code_executor import CodeExecutor, CodeLanguage
from src.agents.coder_agent import CoderAgent
from src.agents.reviewer_agent import ReviewerAgent


class TestEventBus:
    """事件总线测试"""

    @pytest.mark.asyncio
    async def test_subscribe_publish(self):
        """测试订阅和发布"""
        bus = EventBus()
        received = []

        async def handler(event):
            received.append(event)

        await bus.subscribe(EventType.TASK_CREATED, handler)
        await bus.publish(Event(EventType.TASK_CREATED, {"test": "data"}))

        assert len(received) == 1
        assert received[0].data["test"] == "data"

    @pytest.mark.asyncio
    async def test_wildcard_subscription(self):
        """测试通配符订阅"""
        bus = EventBus()
        received = []

        async def handler(event):
            received.append(event)

        await bus.subscribe_wildcard(handler)
        await bus.publish(Event(EventType.AGENT_REGISTERED, {"id": 1}))
        await bus.publish(Event(EventType.TASK_CREATED, {"id": 2}))

        assert len(received) == 2


class TestCodeExecutor:
    """代码执行器测试"""

    @pytest.mark.asyncio
    async def test_python_execution(self):
        """测试Python代码执行"""
        executor = CodeExecutor()
        result = await executor.execute(
            code="print('Hello, World!')",
            language=CodeLanguage.PYTHON
        )

        assert result.status.value == "success"
        assert "Hello, World!" in result.stdout

    @pytest.mark.asyncio
    async def test_javascript_execution(self):
        """测试JavaScript代码执行"""
        executor = CodeExecutor()
        result = await executor.execute(
            code="console.log('Hello from JS!');",
            language=CodeLanguage.JAVASCRIPT
        )

        assert result.status.value == "success"

    @pytest.mark.asyncio
    async def test_execution_timeout(self):
        """测试执行超时"""
        executor = CodeExecutor()
        result = await executor.execute(
            code="import time; time.sleep(100)",
            language=CodeLanguage.PYTHON,
            config=ExecutionConfig(timeout=1)
        )

        assert result.status.value == "timeout"

    @pytest.mark.asyncio
    async def test_execution_error(self):
        """测试执行错误"""
        executor = CodeExecutor()
        result = await executor.execute(
            code="raise ValueError('Test error')",
            language=CodeLanguage.PYTHON
        )

        assert result.status.value == "failed"
        assert "ValueError" in result.stderr


class TestTaskScheduler:
    """任务调度器测试"""

    @pytest.mark.asyncio
    async def test_task_creation(self):
        """测试任务创建"""
        bus = EventBus()
        scheduler = TaskScheduler(bus)

        task = await scheduler.create_task(
            title="Test Task",
            description="A test task",
            task_type="general"
        )

        assert task.title == "Test Task"
        assert task.task_id is not None
        assert len(scheduler.tasks) == 1

    @pytest.mark.asyncio
    async def test_task_assignment(self):
        """测试任务分配"""
        bus = EventBus()
        scheduler = TaskScheduler(bus)

        # 创建虚拟Agent
        agent = Agent(
            agent_id="test_agent",
            name="Test Agent",
            role=AgentRole.CODER,
            capabilities=AgentCapability(languages=["python"])
        )

        scheduler.register_agent(agent)

        task = await scheduler.create_task(
            title="Test Task",
            description="Test"
        )

        # 分配任务
        success = await scheduler.assign_task(task.task_id, agent.agent_id)
        assert success is True
        assert task.assigned_agent == agent.agent_id


class TestCoderAgent:
    """程序员Agent测试"""

    @pytest.mark.asyncio
    async def test_process_task(self):
        """测试处理任务"""
        agent = CoderAgent(
            agent_id="test_coder",
            name="Test Coder"
        )

        task = {
            "task_id": "test_1",
            "description": "Implement a function",
            "task_type": "function",
            "input_data": {
                "language": "python",
                "description": "Add two numbers"
            }
        }

        result = await agent.process_task(task)

        assert "code" in result or "error" in result

    @pytest.mark.asyncio
    async def test_code_generation(self):
        """测试代码生成"""
        agent = CoderAgent(
            agent_id="test_coder",
            name="Test Coder"
        )

        task = {
            "task_id": "test_2",
            "description": "api",
            "input_data": {
                "language": "python",
                "framework": "fastapi"
            }
        }

        result = await agent.process_task(task)

        assert result.get("status") == "success"
        assert "code" in result


class TestReviewerAgent:
    """评审员Agent测试"""

    @pytest.mark.asyncio
    async def test_code_review(self):
        """测试代码审查"""
        agent = ReviewerAgent(
            agent_id="test_reviewer",
            name="Test Reviewer"
        )

        code = '''
def add(a, b):
    return a + b

result = add(1, 2)
print(result)
'''

        result = await agent.review_code(code, "python")

        assert "summary" in result
        assert "issues" in result
        assert "quality_score" in result


class TestMessageSystem:
    """消息系统测试"""

    def test_message_creation(self):
        """测试消息创建"""
        msg = Message(
            sender_id="sender_1",
            recipient_id="recipient_1",
            content={"data": "test"},
            message_type=MessageType.TASK_REQUEST
        )

        assert msg.sender_id == "sender_1"
        assert msg.message_id is not None

    def test_message_reply(self):
        """测试消息回复"""
        msg = Message(
            sender_id="sender_1",
            recipient_id="recipient_1",
            content={"data": "test"},
            message_type=MessageType.TASK_REQUEST
        )

        reply = msg.create_reply(
            content={"result": "success"},
            message_type=MessageType.TASK_RESPONSE
        )

        assert reply.sender_id == "recipient_1"
        assert reply.recipient_id == "sender_1"
        assert reply.correlation_id == msg.message_id


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流"""
        # 初始化组件
        bus = EventBus()
        executor = CodeExecutor()
        scheduler = TaskScheduler(bus)

        # 创建Agent
        coder = CoderAgent(
            agent_id="coder_1",
            name="Coder",
            executor=executor
        )

        scheduler.register_agent(coder)

        # 创建任务
        task = await scheduler.create_task(
            title="Write Hello World",
            description="Implement hello world",
            input_data={
                "language": "python"
            }
        )

        # 启动调度器
        await scheduler.start()

        # 等待任务处理
        await asyncio.sleep(3)

        # 停止调度器
        await scheduler.stop()

        # 验证结果
        assert task.task_id in scheduler.tasks


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
