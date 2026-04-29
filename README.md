---
AIGC:
    ContentProducer: Minimax Agent AI
    ContentPropagator: Minimax Agent AI
    Label: AIGC
    ProduceID: "00000000000000000000000000000000"
    PropagateID: "00000000000000000000000000000000"
    ReservedCode1: 3045022100c4592a7846dc75b56bb33e0b801a404a02d8adfd3c3e57844ef4f7059e34e8020220448619adafbef36ebddb6007495c9499c31a8688b75e1a4c5e97a129d212f753
    ReservedCode2: 304402204ba1ca6573b0dfcef54275e0c9f00e43ff3e6ac758515a188195fad5d99394400220219fbf4a2744a2253212bfb5875e6dacdff91ab66f17bcbe4c0d95b82bc89e0e
---

# Multi-Agent Collaborative Auto-Programming System
# 多智能体协同自动编程系统

一个基于多智能体协作的自动编程系统，支持架构设计、代码编写、代码审查、调试等多种任务。

## 功能特性

- **多角色Agent**: 架构师、程序员、评审员、调试员等专业角色
- **任务调度**: 智能任务分配和优先级管理
- **代码执行**: 支持多种编程语言的代码执行环境
- **协作工作流**: 预定义的工作流模板（代码开发、Bug修复、代码审查等）
- **Web管理界面**: 可视化的系统监控和任务管理
- **事件驱动**: 基于事件总线的松耦合通信

## 安装

```bash
# 克隆项目
git clone <repository-url>
cd multi_agent_coding_system

# 安装依赖
pip install -r requirements.txt
```

## 使用方法

### 演示模式

```bash
python main.py demo
```

### Web服务模式

```bash
python main.py web --port 5000
```

### 命令行模式

```bash
# 查看所有Agent
python main.py agents

# 查看系统状态
python main.py status
```

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Multi-Agent System                     │
├─────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │
│  │Architect│  │  Coder  │  │ Reviewer│  │ Debugger│    │
│  │  Agent  │  │  Agent  │  │  Agent  │  │  Agent  │    │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘    │
│       │            │            │            │          │
│       └────────────┴─────┬──────┴────────────┘          │
│                          │                              │
│                    ┌─────▼─────┐                        │
│                    │ Orchestrator│                       │
│                    └─────┬─────┘                        │
│                          │                              │
│  ┌───────────────────────┼───────────────────────┐     │
│  │                       │                        │     │
│  ▼                       ▼                        ▼     │
│ ┌──────────┐      ┌────────────┐       ┌────────────┐  │
│ │ Task     │      │ Code       │       │ Event      │  │
│ │ Scheduler│      │ Executor   │       │ Bus        │  │
│ └──────────┘      └────────────┘       └────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Web Management Interface              │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Agent角色

### 架构师 (Architect)
- 系统架构设计
- 技术选型建议
- 数据库设计
- API设计

### 程序员 (Coder)
- 代码编写实现
- API开发
- 测试代码生成

### 评审员 (Reviewer)
- 代码质量审查
- 安全问题检测
- 性能分析
- 最佳实践检查

### 调试员 (Debugger)
- 问题定位
- 错误分析
- 修复建议

## 工作流程

### 代码开发流程
1. 架构师进行系统设计
2. 程序员根据设计编写代码
3. 评审员审查代码质量
4. 如有问题，调试员介入修复
5. 代码验证和测试

## API使用

```python
import asyncio
from src.system import create_system

async def main():
    # 创建系统
    system = await create_system()

    # 创建代码开发任务
    task_id = await system.create_code_task(
        requirement="Create a user login API",
        language="python",
        framework="fastapi"
    )

    # 执行代码
    result = await system.execute_code(
        code="print('Hello, World!')",
        language="python"
    )

    # 获取系统状态
    status = system.get_status()

    # 关闭系统
    await system.shutdown()

asyncio.run(main())
```

## 配置说明

编辑 `config.json` 文件：

```json
{
    "agents": {
        "coder": {
            "count": 3,  // 程序员数量
            "max_concurrent_tasks": 3
        }
    },
    "executor": {
        "timeout": 60,  // 执行超时（秒）
        "memory_limit": 1024  // 内存限制（MB）
    }
}
```

## License

MIT License
