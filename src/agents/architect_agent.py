"""
Architect Agent - 架构师Agent
负责系统设计、技术选型和架构规划
"""

from typing import Dict, List, Optional, Any
import asyncio
from ..core.agent import Agent, AgentRole, AgentStatus, AgentCapability
from ..core.message import Message, MessageType


class ArchitectAgent(Agent):
    """
    架构师Agent
    专注于系统架构设计和技术决策
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        llm_provider: Optional[callable] = None
    ):
        capabilities = AgentCapability(
            languages=["python", "javascript", "typescript", "go", "rust"],
            frameworks=["react", "vue", "fastapi", "django", "spring"],
            expertise=["system_design", "microservices", "database_design", "api_design"],
            max_concurrent_tasks=2
        )
        super().__init__(agent_id, name, AgentRole.ARCHITECT, capabilities, llm_provider)

        # 架构设计模式库
        self.design_patterns = [
            "singleton", "factory", "observer", "strategy", "decorator",
            "adapter", "facade", "proxy", "mvc", "mvvm", "clean_architecture"
        ]

        # 注册消息处理器
        self.register_handler(MessageType.TASK_REQUEST.value, self._handle_task_request)

    async def think(self, context: Dict) -> str:
        """
        思考过程 - 分析需求并设计架构

        Args:
            context: 包含需求描述的上下文

        Returns:
            思考结果和架构建议
        """
        requirement = context.get("requirement", "")
        constraints = context.get("constraints", {})
        preferences = context.get("preferences", {})

        # 如果有LLM提供者，使用AI进行架构分析
        if self.llm_provider:
            prompt = f"""
            As a software architect, analyze the following requirement and provide an architecture design:

            Requirement: {requirement}
            Constraints: {constraints}
            Preferences: {preferences}

            Provide:
            1. High-level architecture recommendation
            2. Technology stack suggestions
            3. Key design patterns to use
            4. Data modeling approach
            5. API design strategy
            """
            try:
                response = await self.llm_provider(prompt)
                return response
            except Exception as e:
                return f"Architecture analysis: {str(e)}"

        # 默认分析逻辑
        return self._basic_architecture_analysis(requirement, constraints)

    def _basic_architecture_analysis(self, requirement: str, constraints: Dict) -> str:
        """基础架构分析"""
        # 简单的关键词匹配分析
        has_real_time = any(kw in requirement.lower() for kw in ["real-time", "websocket", "live", "streaming"])
        has_ml = any(kw in requirement.lower() for kw in ["ml", "machine learning", "ai", "prediction"])
        has_analytics = any(kw in requirement.lower() for kw in ["analytics", "dashboard", "report", "metric"])

        recommendations = []

        if has_real_time:
            recommendations.append("- Consider using WebSocket or Server-Sent Events for real-time updates")
        if has_ml:
            recommendations.append("- Integrate ML pipeline with model serving infrastructure")
        if has_analytics:
            recommendations.append("- Use data warehouse or OLAP database for analytics")

        return f"""
        Architecture Analysis:
        {chr(10).join(recommendations) if recommendations else '- Standard web application architecture recommended'}

        Suggested Layers:
        - Presentation Layer (Frontend)
        - Application Layer (Business Logic)
        - Data Layer (Database + Cache)
        """

    async def process_task(self, task: Dict) -> Dict:
        """
        处理架构设计任务

        Args:
            task: 任务描述

        Returns:
            任务结果
        """
        await self.update_status(AgentStatus.WORKING, "Processing architecture design")
        self.current_task = task.get("task_id")

        task_type = task.get("description", "").lower()

        try:
            if "design" in task_type or "architecture" in task_type:
                result = await self._design_architecture(task)
            elif "analyze" in task_type:
                result = await self._analyze_requirement(task)
            elif "review" in task_type:
                result = await self._review_architecture(task)
            else:
                result = await self._generic_architecture_task(task)

            await self.update_status(AgentStatus.SUCCESS, "Task completed")
            self.metrics["tasks_completed"] += 1

            return result

        except Exception as e:
            await self.update_status(AgentStatus.FAILED, str(e))
            self.metrics["tasks_failed"] += 1
            return {"error": str(e)}

    async def _design_architecture(self, task: Dict) -> Dict:
        """设计系统架构"""
        context = {
            "requirement": task.get("input_data", {}).get("requirement", ""),
            "constraints": task.get("input_data", {}).get("constraints", {}),
            "preferences": task.get("input_data", {}).get("preferences", {})
        }

        analysis = await self.think(context)

        # 生成架构文档
        architecture = {
            "overview": analysis,
            "components": [
                {
                    "name": "Frontend",
                    "type": "client",
                    "responsibilities": ["UI rendering", "User interaction", "State management"]
                },
                {
                    "name": "API Gateway",
                    "type": "gateway",
                    "responsibilities": ["Request routing", "Authentication", "Rate limiting"]
                },
                {
                    "name": "Application Service",
                    "type": "service",
                    "responsibilities": ["Business logic", "Data validation", "Workflow orchestration"]
                },
                {
                    "name": "Data Layer",
                    "type": "storage",
                    "responsibilities": ["Data persistence", "Query optimization", "Data integrity"]
                }
            ],
            "data_flow": "Frontend → API Gateway → Application Service → Data Layer",
            "design_patterns": self._suggest_patterns(context.get("requirement", "")),
            "technology_recommendations": self._suggest_tech_stack(context)
        }

        self.add_to_memory(f"architecture_{task.get('task_id')}", architecture)

        return {
            "status": "success",
            "architecture": architecture,
            "analysis": analysis
        }

    async def _analyze_requirement(self, task: Dict) -> Dict:
        """分析需求"""
        requirement = task.get("input_data", {}).get("requirement", "")

        return {
            "status": "success",
            "analysis": {
                "functional_requirements": self._extract_functional_requirements(requirement),
                "non_functional_requirements": self._extract_non_functional_requirements(requirement),
                "risks": self._identify_risks(requirement),
                "complexity": self._estimate_complexity(requirement)
            }
        }

    async def _review_architecture(self, task: Dict) -> Dict:
        """评审架构"""
        architecture = task.get("input_data", {}).get("architecture", {})

        return {
            "status": "success",
            "review": {
                "strengths": self._identify_strengths(architecture),
                "weaknesses": self._identify_weaknesses(architecture),
                "suggestions": self._generate_suggestions(architecture)
            }
        }

    async def _generic_architecture_task(self, task: Dict) -> Dict:
        """通用架构任务"""
        return {
            "status": "success",
            "message": "Architecture task processed",
            "context": task.get("context", {})
        }

    def _suggest_patterns(self, requirement: str) -> List[str]:
        """建议设计模式"""
        patterns = []
        req_lower = requirement.lower()

        if "user" in req_lower and "auth" in req_lower:
            patterns.append("Strategy (Authentication)")
        if "notify" in req_lower or "subscribe" in req_lower:
            patterns.append("Observer")
        if "payment" in req_lower or "order" in req_lower:
            patterns.append("Factory + State Machine")
        if any(kw in req_lower for kw in ["cache", "memory"]):
            patterns.append("Proxy + Cache")

        return patterns or ["MVC", "Repository"]

    def _suggest_tech_stack(self, context: Dict) -> Dict:
        """建议技术栈"""
        return {
            "frontend": ["React 18", "TypeScript", "TailwindCSS"],
            "backend": ["FastAPI", "PostgreSQL", "Redis"],
            "devops": ["Docker", "Kubernetes", "CI/CD"],
            "monitoring": ["Prometheus", "Grafana", "ELK Stack"]
        }

    def _extract_functional_requirements(self, requirement: str) -> List[str]:
        """提取功能需求"""
        # 简单实现，实际需要NLP处理
        return ["User authentication", "Data management", "API integration"]

    def _extract_non_functional_requirements(self, requirement: str) -> Dict:
        """提取非功能需求"""
        return {
            "performance": "响应时间 < 200ms",
            "scalability": "支持水平扩展",
            "availability": "99.9% uptime",
            "security": "数据加密传输"
        }

    def _identify_risks(self, requirement: str) -> List[str]:
        """识别风险"""
        return ["技术栈选择风险", "进度风险", "人员风险"]

    def _estimate_complexity(self, requirement: str) -> str:
        """评估复杂度"""
        words = len(requirement.split())
        if words > 100:
            return "High"
        elif words > 50:
            return "Medium"
        return "Low"

    def _identify_strengths(self, architecture: Dict) -> List[str]:
        return ["模块化设计", "清晰的职责分离"]

    def _identify_weaknesses(self, architecture: Dict) -> List[str]:
        return ["可能缺少容错机制"]

    def _generate_suggestions(self, architecture: Dict) -> List[str]:
        return ["建议添加监控和日志系统", "考虑添加熔断器模式"]

    async def _handle_task_request(self, message: Message) -> None:
        """处理任务请求消息"""
        task_data = message.content.get("task", {})
        result = await self.process_task(task_data)

        # 发送响应
        response = message.create_reply(
            content={"result": result},
            message_type=MessageType.TASK_RESPONSE
        )
        return response

    async def design_api(
        self,
        endpoints: List[Dict],
        authentication: str = "jwt"
    ) -> Dict:
        """
        设计API架构

        Args:
            endpoints: 端点列表
            authentication: 认证方式

        Returns:
            API设计文档
        """
        api_design = {
            "base_url": "/api/v1",
            "authentication": {
                "type": authentication,
                "header": "Authorization"
            },
            "endpoints": [],
            "common_responses": {
                "200": {"description": "Success"},
                "400": {"description": "Bad Request"},
                "401": {"description": "Unauthorized"},
                "404": {"description": "Not Found"},
                "500": {"description": "Internal Server Error"}
            }
        }

        for endpoint in endpoints:
            api_design["endpoints"].append({
                "path": endpoint.get("path"),
                "method": endpoint.get("method", "GET"),
                "description": endpoint.get("description", ""),
                "parameters": endpoint.get("parameters", []),
                "request_body": endpoint.get("request_body"),
                "responses": endpoint.get("responses", api_design["common_responses"])
            })

        return api_design

    async def design_database_schema(
        self,
        entities: List[Dict]
    ) -> Dict:
        """
        设计数据库架构

        Args:
            entities: 实体列表

        Returns:
            数据库架构文档
        """
        schema = {
            "tables": [],
            "relationships": []
        }

        for entity in entities:
            table = {
                "name": entity.get("name"),
                "columns": entity.get("columns", []),
                "primary_key": entity.get("primary_key", "id"),
                "indexes": entity.get("indexes", [])
            }
            schema["tables"].append(table)

            # 添加关系
            for relation in entity.get("relations", []):
                schema["relationships"].append({
                    "from": entity.get("name"),
                    "to": relation.get("target"),
                    "type": relation.get("type", "one-to-many"),
                    "foreign_key": relation.get("foreign_key")
                })

        return schema
