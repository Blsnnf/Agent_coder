# 多Agent自动编程系统 - 开发指南

## 项目概述
基于多智能体协作的自动编程系统，支持架构设计、代码编写、代码审查、调试等多种任务。

## 技术栈
- Python 3.12+
- Flask (Web框架)
- Pydantic (数据验证)
- asyncio (异步编程)

## 项目结构
```
src/
├── system.py              # 主系统入口
├── orchestrator.py        # 协调器（已内嵌到system.py）
├── core/
│   ├── agent.py           # Agent基类
│   ├── message.py         # 消息系统
│   └── event_bus.py       # 事件总线
├── agents/
│   ├── architect_agent.py # 架构师
│   ├── coder_agent.py     # 程序员
│   ├── reviewer_agent.py  # 评审员
│   └── debugger_agent.py  # 调试员
├── scheduler/
│   └── task_scheduler.py  # 任务调度器
├── executor/
│   └── __init__.py        # 代码执行器
└── web/
    └── __init__.py        # Web界面
```

## 关键类和接口

### Agent (core/agent.py)
- `process_task(task: Dict) -> Dict`: 处理任务
- `think(context: Dict) -> str`: 思考过程
- `receive_message(message: Message)`: 接收消息
- `send_message(recipient_id, content, message_type) -> Message`: 发送消息

### TaskScheduler (scheduler/task_scheduler.py)
- `create_task(title, description, task_type, priority, input_data) -> Task`
- `assign_task(task_id, agent_id) -> bool`
- `get_stats() -> Dict`

### CodeExecutor (executor/__init__.py)
- `execute(code, language, stdin, config) -> ExecutionResult`
- `CodeLanguage`: Python, JavaScript, TypeScript, Java, C, CPP, Go, Rust, Bash等

## 工作流程

1. **代码开发流程**: 架构师设计 -> 程序员编码 -> 评审员审查 -> 调试员修复
2. **Bug修复流程**: 定位问题 -> 分析原因 -> 生成修复 -> 验证
3. **代码审查流程**: 提交代码 -> 自动化审查 -> 生成报告

## 待完善功能

1. **MiniMax API集成**: 将MiniMax大模型集成到Agent的think和process_task方法
2. **任务执行闭环**: 让Agent真正执行分配的任务并返回结果
3. **Web界面增强**: 实时任务状态、Agent协作可视化
4. **持久化存储**: 支持保存项目、任务历史

## 运行命令
```bash
# 演示模式
python main.py demo

# Web服务模式
python main.py web --port 5000

# 查看Agent列表
python main.py agents

# 查看系统状态
python main.py status
```
