"""
Web Module - Web模块
提供Web管理和监控界面
"""

from flask import Blueprint, render_template, request, jsonify
from typing import Dict, Any
import asyncio

web_bp = Blueprint('web', __name__, template_folder='templates')


def create_web_app(scheduler: 'TaskScheduler', agents: Dict[str, 'Agent'], executor: 'CodeExecutor'):
    """
    创建Web应用

    Args:
        scheduler: 任务调度器
        agents: Agent字典
        executor: 代码执行器

    Returns:
        Flask Blueprint
    """
    web_bp.scheduler = scheduler
    web_bp.agents = agents
    web_bp.executor = executor

    @web_bp.route('/')
    def index():
        """主页"""
        return render_template('index.html')

    @web_bp.route('/api/agents')
    def get_agents():
        """获取所有Agent"""
        agents_data = {
            agent_id: agent.to_dict()
            for agent_id, agent in web_bp.agents.items()
        }
        return jsonify({
            "status": "success",
            "agents": agents_data,
            "count": len(agents_data)
        })

    @web_bp.route('/api/agents/<agent_id>')
    def get_agent(agent_id):
        """获取单个Agent"""
        agent = web_bp.agents.get(agent_id)
        if not agent:
            return jsonify({"status": "error", "message": "Agent not found"}), 404

        return jsonify({
            "status": "success",
            "agent": agent.to_dict(),
            "metrics": agent.get_metrics(),
            "capabilities": agent.get_capabilities_summary()
        })

    @web_bp.route('/api/tasks', methods=['GET', 'POST'])
    def handle_tasks():
        """处理任务请求"""
        if request.method == 'POST':
            data = request.json
            task = asyncio.run(web_bp.scheduler.create_task(
                title=data.get('title', ''),
                description=data.get('description', ''),
                task_type=data.get('task_type', 'general'),
                priority=data.get('priority', 1),
                input_data=data.get('input_data', {})
            ))
            return jsonify({
                "status": "success",
                "task": task.to_dict()
            })
        else:
            # GET: 返回所有任务
            tasks = {
                task_id: task.to_dict()
                for task_id, task in web_bp.scheduler.tasks.items()
            }
            return jsonify({
                "status": "success",
                "tasks": tasks,
                "stats": web_bp.scheduler.get_stats()
            })

    @web_bp.route('/api/tasks/<task_id>')
    def get_task(task_id):
        """获取任务详情"""
        task = web_bp.scheduler.get_task_status(task_id)
        if not task:
            return jsonify({"status": "error", "message": "Task not found"}), 404

        return jsonify({
            "status": "success",
            "task": task
        })

    @web_bp.route('/api/execute', methods=['POST'])
    def execute_code():
        """执行代码"""
        data = request.json
        code = data.get('code', '')
        language = data.get('language', 'python')
        stdin = data.get('stdin', None)

        result = asyncio.run(web_bp.executor.execute(
            code=code,
            language=language,
            stdin=stdin
        ))

        return jsonify({
            "status": "success",
            "result": result.to_dict()
        })

    @web_bp.route('/api/executor/stats')
    def get_executor_stats():
        """获取执行器统计"""
        return jsonify({
            "status": "success",
            "stats": web_bp.executor.get_stats()
        })

    @web_bp.route('/api/stats')
    def get_system_stats():
        """获取系统统计"""
        return jsonify({
            "status": "success",
            "scheduler": web_bp.scheduler.get_stats(),
            "executor": web_bp.executor.get_stats(),
            "event_bus": web_bp.scheduler.event_bus.get_stats() if web_bp.scheduler.event_bus else {},
            "agent_count": len(web_bp.agents),
            "task_count": len(web_bp.scheduler.tasks)
        })

    return web_bp
