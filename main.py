#!/usr/bin/env python3
"""
Multi-Agent Collaborative Auto-Programming System
多智能体协同自动编程系统 - 主入口
"""

import asyncio
import argparse
import sys
from typing import Optional

from src.system import MultiAgentCodingSystem, create_system


async def demo_mode():
    """演示模式"""
    print("\n" + "=" * 60)
    print("🔬 Running in Demo Mode")
    print("=" * 60 + "\n")

    # 创建系统
    system = await create_system()

    # 创建代码开发任务
    print("📝 Creating a code development task...")
    task_id = await system.create_code_task(
        requirement="Create a REST API for user management with CRUD operations",
        language="python",
        framework="fastapi"
    )
    print(f"   Task ID: {task_id}")

    # 等待任务分配
    await asyncio.sleep(1)

    # 执行代码示例
    print("\n⚡ Executing code example...")
    code = '''
def fibonacci(n):
    """Calculate fibonacci number"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print("Fibonacci(10):", fibonacci(10))
'''

    result = await system.execute_code(code, "python")
    print(f"   Status: {result['status']}")
    print(f"   Output: {result['stdout'].strip()}")
    print(f"   Time: {result['execution_time']:.4f}s")

    # 创建代码审查任务
    print("\n🔍 Creating a code review task...")
    code_to_review = '''
def calculate(x, y):
    result = x + y
    return result

z = calculate(10, 20)
print(z)
'''
    review_task_id = await system.create_review_task(code_to_review, "python")
    print(f"   Review Task ID: {review_task_id}")

    # 创建调试任务
    print("\n🔧 Creating a debug task...")
    debug_task_id = await system.create_debug_task(
        error="NameError: name 'undefined_var' is not defined",
        code='print(undefined_var)',
        language="python"
    )
    print(f"   Debug Task ID: {debug_task_id}")

    # 显示系统状态
    print("\n📊 System Status:")
    status = system.get_status()
    print(f"   Agents: {status['agent_count']}")
    print(f"   Total Tasks: {status['scheduler']['total_tasks']}")
    print(f"   Completed: {status['scheduler']['completed_tasks']}")
    print(f"   Code Executions: {status['executor']['total_executions']}")

    # 关闭系统
    await system.shutdown()

    print("\n✅ Demo completed successfully!")


async def web_mode(host: str = "0.0.0.0", port: int = 5000):
    """Web服务模式"""
    from flask import Flask
    from src.web import create_web_app

    print("\n" + "=" * 60)
    print("🌐 Running in Web Mode")
    print("=" * 60 + "\n")

    # 创建系统
    system = await create_system()

    # 创建Flask应用
    app = Flask(__name__)

    # 注册Web蓝图
    web_bp = create_web_app(
        scheduler=system.orchestrator.task_scheduler,
        agents=system.orchestrator.agents,
        executor=system.code_executor
    )
    app.register_blueprint(web_bp)

    print(f"🚀 Server starting on http://{host}:{port}")
    print(f"📊 Dashboard: http://{host}:{port}/")

    try:
        app.run(host=host, port=port, debug=False)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    finally:
        await system.shutdown()


async def cli_mode(command: str):
    """命令行交互模式"""
    system = await create_system()

    commands = {
        "agents": lambda: list_agents(system),
        "status": lambda: show_status(system),
        "help": lambda: show_help(),
    }

    if command in commands:
        await commands[command]()
    else:
        print(f"Unknown command: {command}")
        await show_help()

    await system.shutdown()


async def list_agents(system: MultiAgentCodingSystem):
    """列出所有Agent"""
    print("\n👥 Registered Agents:")
    print("-" * 40)
    for agent in system.orchestrator.agents.values():
        print(f"   {agent.name}")
        print(f"      Role: {agent.role.value}")
        print(f"      Status: {agent.status.value}")
        caps = agent.get_capabilities_summary()
        print(f"      Languages: {', '.join(caps['languages'][:3])}")
        print()


async def show_status(system: MultiAgentCodingSystem):
    """显示系统状态"""
    status = system.get_status()
    print("\n📊 System Status:")
    print("-" * 40)
    print(f"   Total Agents: {status['agent_count']}")
    print(f"   Scheduler Tasks: {status['scheduler']['total_tasks']}")
    print(f"   Completed Tasks: {status['scheduler']['completed_tasks']}")
    print(f"   Code Executions: {status['executor']['total_executions']}")
    print()


async def show_help():
    """显示帮助"""
    print("""
Available Commands:
    python main.py demo      - Run demo mode
    python main.py web       - Run web server mode
    python main.py agents     - List all agents
    python main.py status     - Show system status

Examples:
    python main.py demo
    python main.py web --host 0.0.0.0 --port 5000
    python main.py agents
    """)


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Agent Collaborative Auto-Programming System"
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="demo",
        choices=["demo", "web", "agents", "status", "help"],
        help="Command to run"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Web server host (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Web server port (default: 5000)"
    )

    args = parser.parse_args()

    if args.command == "web":
        asyncio.run(web_mode(args.host, args.port))
    elif args.command == "demo":
        asyncio.run(demo_mode())
    else:
        asyncio.run(cli_mode(args.command))


if __name__ == "__main__":
    main()
