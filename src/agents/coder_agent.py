"""
Coder Agent - 程序员Agent
负责代码编写和实现
"""

from typing import Dict, List, Optional, Any
import asyncio
import re
from ..core.agent import Agent, AgentRole, AgentStatus, AgentCapability
from ..core.message import Message, MessageType
from ..executor import CodeExecutor, CodeLanguage, ExecutionConfig


class CoderAgent(Agent):
    """
    程序员Agent
    专注于代码编写和实现
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        llm_provider: Optional[callable] = None,
        executor: Optional[CodeExecutor] = None
    ):
        capabilities = AgentCapability(
            languages=["python", "javascript", "typescript", "java", "go", "rust", "c"],
            frameworks=["react", "vue", "fastapi", "django", "spring", "express"],
            expertise=["backend_development", "frontend_development", "api_development", "database"],
            max_concurrent_tasks=3
        )
        super().__init__(agent_id, name, AgentRole.CODER, capabilities, llm_provider)

        self.executor = executor or CodeExecutor()

        # 代码模板库
        self.code_templates = {
            "crud_api": self._get_crud_api_template(),
            "class": self._get_class_template(),
            "function": self._get_function_template(),
            "test": self._get_test_template()
        }

        # 注册消息处理器
        self.register_handler(MessageType.TASK_REQUEST.value, self._handle_task_request)
        self.register_handler(MessageType.CODE_REVIEW.value, self._handle_code_review)

    async def think(self, context: Dict) -> str:
        """
        思考过程 - 分析任务并制定实现方案

        Args:
            context: 上下文信息

        Returns:
            实现方案
        """
        task = context.get("task", {})
        language = task.get("language", "python")
        requirement = task.get("description", "")

        if self.llm_provider:
            prompt = f"""
            As a senior programmer, implement the following feature:

            Requirement: {requirement}
            Language: {language}

            Provide clean, well-documented code with:
            1. Clear function/class structure
            2. Error handling
            3. Type hints (if applicable)
            4. Docstrings
            """
            try:
                response = await self.llm_provider(prompt)
                return response
            except Exception as e:
                return f"Implementation planning: {str(e)}"

        return self._basic_implementation_plan(task)

    def _basic_implementation_plan(self, task: Dict) -> str:
        """基础实现计划"""
        task_type = task.get("task_type", "general")

        plans = {
            "api": "1. Define data models\n2. Create API endpoints\n3. Add request validation\n4. Implement error handling",
            "function": "1. Define function signature\n2. Implement logic\n3. Add edge case handling\n4. Write docstring",
            "class": "1. Define class structure\n2. Implement methods\n3. Add properties\n4. Include __init__ and __str__"
        }

        return plans.get(task_type, "1. Analyze requirement\n2. Write code\n3. Add tests\n4. Document")

    async def process_task(self, task: Dict) -> Dict:
        """
        处理代码编写任务

        Args:
            task: 任务描述

        Returns:
            任务结果
        """
        await self.update_status(AgentStatus.WORKING, "Writing code")
        self.current_task = task.get("task_id")

        task_type = task.get("task_type", task.get("description", "").lower())

        try:
            if "api" in task_type or "endpoint" in task_type:
                result = await self._implement_api(task)
            elif "function" in task_type:
                result = await self._implement_function(task)
            elif "class" in task_type or "object" in task_type:
                result = await self._implement_class(task)
            elif "test" in task_type:
                result = await self._implement_test(task)
            else:
                result = await self._implement_generic(task)

            # 执行代码验证
            if result.get("code"):
                exec_result = await self._validate_code(result["code"], task)
                result["execution"] = exec_result

            await self.update_status(AgentStatus.SUCCESS, "Code written successfully")
            self.metrics["tasks_completed"] += 1

            self.add_to_memory(f"code_{task.get('task_id')}", result)

            return result

        except Exception as e:
            await self.update_status(AgentStatus.FAILED, str(e))
            self.metrics["tasks_failed"] += 1
            return {"error": str(e)}

    async def _implement_api(self, task: Dict) -> Dict:
        """实现API"""
        input_data = task.get("input_data", {})
        language = input_data.get("language", "python")
        framework = input_data.get("framework", "fastapi")

        if framework == "fastapi":
            code = self._generate_fastapi_code(input_data)
        elif framework == "express":
            code = self._generate_express_code(input_data)
        else:
            code = self._generate_generic_api_code(input_data, language)

        return {
            "status": "success",
            "code": code,
            "language": language,
            "framework": framework,
            "files": [
                {"name": f"api.{'py' if language == 'python' else 'js'}", "content": code}
            ]
        }

    async def _implement_function(self, task: Dict) -> Dict:
        """实现函数"""
        input_data = task.get("input_data", {})
        language = input_data.get("language", "python")
        description = input_data.get("description", task.get("description", ""))

        code = self._generate_function_code(description, language)

        return {
            "status": "success",
            "code": code,
            "language": language,
            "function_signature": self._extract_signature(code)
        }

    async def _implement_class(self, task: Dict) -> Dict:
        """实现类"""
        input_data = task.get("input_data", {})
        language = input_data.get("language", "python")
        class_name = input_data.get("class_name", "MyClass")

        code = self._generate_class_code(class_name, language)

        return {
            "status": "success",
            "code": code,
            "language": language,
            "class_name": class_name
        }

    async def _implement_test(self, task: Dict) -> Dict:
        """实现测试"""
        input_data = task.get("input_data", {})
        code_to_test = input_data.get("code", "")
        language = input_data.get("language", "python")
        test_framework = input_data.get("test_framework", "pytest")

        test_code = self._generate_test_code(code_to_test, language, test_framework)

        return {
            "status": "success",
            "code": test_code,
            "language": language,
            "test_framework": test_framework
        }

    async def _implement_generic(self, task: Dict) -> Dict:
        """通用实现"""
        context = {"task": task}
        plan = await self.think(context)

        input_data = task.get("input_data", {})
        language = input_data.get("language", "python")

        code = f"# Generated code\n# Plan: {plan}\n\n"

        if input_data.get("description"):
            code += f'"""\n{input_data.get("description")}\n"""\n\n'

        code += self._get_default_implementation(language)

        return {
            "status": "success",
            "code": code,
            "language": language,
            "plan": plan
        }

    async def _validate_code(self, code: str, task: Dict) -> Dict:
        """验证代码"""
        input_data = task.get("input_data", {})
        language_str = input_data.get("language", "python")

        # 映射语言字符串到枚举
        language_map = {
            "python": CodeLanguage.PYTHON,
            "javascript": CodeLanguage.JAVASCRIPT,
            "typescript": CodeLanguage.TYPESCRIPT,
            "java": CodeLanguage.JAVA,
            "go": CodeLanguage.GO,
            "rust": CodeLanguage.RUST,
            "c": CodeLanguage.C,
            "cpp": CodeLanguage.CPP
        }

        language = language_map.get(language_str.lower(), CodeLanguage.PYTHON)

        # 创建临时测试用例
        test_cases = input_data.get("test_cases", [])

        if test_cases:
            test_result = await self.executor.execute_test(code, language, test_cases)
            return test_result
        else:
            # 简单语法检查
            result = await self.executor.execute(code, language, config=ExecutionConfig(timeout=10))
            return result.to_dict()

    # 代码生成辅助方法
    def _generate_fastapi_code(self, input_data: Dict) -> str:
        """生成FastAPI代码"""
        endpoints = input_data.get("endpoints", [])

        code = '''"""
FastAPI Application
Generated by Multi-Agent Coding System
"""

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

app = FastAPI(
    title="API Service",
    description="Generated by AI Multi-Agent System",
    version="1.0.0"
)

# Request/Response Models
'''

        for endpoint in endpoints:
            model_name = self._to_class_name(endpoint.get("name", "Item"))
            code += f'''
class {model_name}Request(BaseModel):
    """Request model for {endpoint.get('name', 'endpoint')}"""
    pass  # Add fields based on endpoint requirements


class {model_name}Response(BaseModel):
    """Response model for {endpoint.get('name', 'endpoint')}"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
'''

        code += "\n# API Endpoints\n"

        for endpoint in endpoints:
            model_name = self._to_class_name(endpoint.get("name", "Item"))
            method = endpoint.get("method", "GET").lower()
            path = endpoint.get("path", f"/{endpoint.get('name', 'item').lower()}s")

            code += f'''
@app.{method}("{path}")
async def {endpoint.get('name', 'handle')}(request: {model_name}Request = None):
    """{endpoint.get('description', 'Endpoint handler')}"""
    return {{"status": "success", "data": request.dict() if request else {{}}}}
'''

        code += '''
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
        return code

    def _generate_express_code(self, input_data: Dict) -> str:
        """生成Express代码"""
        endpoints = input_data.get("endpoints", [])

        code = '''/**
 * Express API Server
 * Generated by Multi-Agent Coding System
 */

const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

'''

        for endpoint in endpoints:
            method = endpoint.get("method", "GET").lower()
            path = endpoint.get("path", f"/{endpoint.get('name', 'item').lower()}s")

            code += f'''// {endpoint.get('description', 'Endpoint')}
app.{method}('{path}', async (req, res) => {{
    try {{
        const result = {{ status: 'success', data: req.body }};
        res.json(result);
    }} catch (error) {{
        res.status(500).json({{ error: error.message }});
    }}
}});

'''

        code += f'''
app.listen(PORT, () => {{
    console.log(`Server running on port ${{PORT}}`);
}});

module.exports = app;
'''
        return code

    def _generate_generic_api_code(self, input_data: Dict, language: str) -> str:
        """生成通用API代码"""
        if language == "python":
            return self._generate_fastapi_code(input_data)
        else:
            return self._generate_express_code(input_data)

    def _generate_function_code(self, description: str, language: str) -> str:
        """生成函数代码"""
        if language == "python":
            return f'''"""
Function implementation
{description}
"""

def process_data(input_data):
    """
    Process input data according to requirements.

    Args:
        input_data: Input data to process

    Returns:
        Processed result
    """
    # TODO: Implement the function logic
    result = input_data
    return result


if __name__ == "__main__":
    # Test the function
    test_data = {{"example": "data"}}
    print(process_data(test_data))
'''
        else:
            return f'''// Function implementation
// {description}

function processData(inputData) {{
    // TODO: Implement the function logic
    const result = inputData;
    return result;
}}

// Test
console.log(processData({{example: "data"}}));
'''

    def _generate_class_code(self, class_name: str, language: str) -> str:
        """生成类代码"""
        if language == "python":
            return f'''"""
{class_name} implementation
"""

class {class_name}:
    """
    A class representing {class_name}.
    """

    def __init__(self, **kwargs):
        """Initialize the {class_name} instance."""
        self.id = kwargs.get('id')
        self._data = kwargs

    def __repr__(self) -> str:
        return f"{class_name}(id={{self.id}})"

    def __str__(self) -> str:
        return f"{class_name} instance"

    @property
    def data(self):
        return self._data

    def to_dict(self) -> dict:
        """Convert instance to dictionary."""
        return {{"id": self.id, "data": self._data}}

    @classmethod
    def from_dict(cls, data: dict) -> "{class_name}":
        """Create instance from dictionary."""
        return cls(**data)
'''

    def _generate_test_code(self, code: str, language: str, test_framework: str) -> str:
        """生成测试代码"""
        if test_framework == "pytest" or language == "python":
            return f'''"""
Test suite for the implementation
"""

import pytest


class TestImplementation:
    """Test cases for the implementation."""

    def test_basic_functionality(self):
        """Test basic functionality."""
        # TODO: Add actual test
        assert True

    def test_edge_cases(self):
        """Test edge cases."""
        # TODO: Add edge case tests
        assert True

    def test_error_handling(self):
        """Test error handling."""
        # TODO: Add error handling tests
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''
        else:
            return f'''/**
 * Test suite for the implementation
 */

const {{ describe, it, expect }} = require('jest');

describe('Implementation Tests', () => {{
    it('should pass basic test', () => {{
        expect(true).toBe(true);
    }});
}});
'''

    def _get_default_implementation(self, language: str) -> str:
        """获取默认实现"""
        if language == "python":
            return '''# Main implementation
def main():
    """Main entry point"""
    print("Hello from Multi-Agent Coding System!")

if __name__ == "__main__":
    main()
'''
        else:
            return '''// Main implementation
function main() {
    console.log("Hello from Multi-Agent Coding System!");
}

main();
'''

    def _to_class_name(self, name: str) -> str:
        """转换为类名格式"""
        return ''.join(word.capitalize() for word in re.split(r'[_\s]+', name))

    def _extract_signature(self, code: str) -> str:
        """提取函数签名"""
        match = re.search(r'def (\w+)\s*\((.*?)\)', code)
        if match:
            return f"{match.group(1)}({match.group(2)})"
        return ""

    # 模板获取方法
    def _get_crud_api_template(self) -> str:
        return self._generate_fastapi_code({"endpoints": []})

    def _get_class_template(self) -> str:
        return self._generate_class_code("MyClass", "python")

    def _get_function_template(self) -> str:
        return self._generate_function_code("Function", "python")

    def _get_test_template(self) -> str:
        return self._generate_test_code("", "python", "pytest")

    # 消息处理
    async def _handle_task_request(self, message: Message) -> Message:
        """处理任务请求"""
        task_data = message.content.get("task", {})
        result = await self.process_task(task_data)

        return message.create_reply(
            content={"result": result},
            message_type=MessageType.TASK_RESPONSE
        )

    async def _handle_code_review(self, message: Message) -> Message:
        """处理代码审查请求"""
        code = message.content.get("code", "")
        language = message.content.get("language", "python")

        return message.create_reply(
            content={"review": self._basic_code_review(code, language)},
            message_type=MessageType.CODE_SUGGESTION
        )

    def _basic_code_review(self, code: str, language: str) -> Dict:
        """基础代码审查"""
        issues = []

        # 检查常见问题
        if "TODO" in code:
            issues.append({"severity": "info", "message": "TODO comments found"})
        if "except:" in code:
            issues.append({"severity": "warning", "message": "Bare except clause found"})
        if language == "python" and "import *" in code:
            issues.append({"severity": "warning", "message": "Wildcard import found"})

        return {
            "issues": issues,
            "line_count": len(code.split('\n')),
            "recommendations": ["Consider adding more documentation", "Add type hints"]
        }
