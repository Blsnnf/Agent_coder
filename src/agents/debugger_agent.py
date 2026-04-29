"""
Debugger Agent - 调试员Agent
负责问题定位、错误分析和修复建议
"""

from typing import Dict, List, Optional, Any, Tuple
import re
import traceback
from dataclasses import dataclass
from ..core.agent import Agent, AgentRole, AgentStatus, AgentCapability
from ..core.message import Message, MessageType


@dataclass
class BugInfo:
    """Bug信息"""
    bug_type: str
    severity: str  # critical, high, medium, low
    line: Optional[int] = None
    message: str = ""
    cause: str = ""
    suggestion: str = ""
    stack_trace: Optional[str] = None


class DebuggerAgent(Agent):
    """
    调试员Agent
    专注于问题定位和错误修复
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        llm_provider: Optional[callable] = None
    ):
        capabilities = AgentCapability(
            languages=["python", "javascript", "typescript", "java", "go"],
            frameworks=["django", "fastapi", "react", "vue", "express"],
            expertise=["debugging", "troubleshooting", "error_handling", "performance_analysis"],
            max_concurrent_tasks=3
        )
        super().__init__(agent_id, name, AgentRole.DEBUGGER, capabilities, llm_provider)

        # 常见错误模式
        self.error_patterns = self._initialize_error_patterns()

        # 注册消息处理器
        self.register_handler(MessageType.BUG_REPORT.value, self._handle_bug_report)
        self.register_handler(MessageType.TASK_REQUEST.value, self._handle_task_request)
        self.register_handler(MessageType.TASK_ERROR.value, self._handle_task_error)

    def _initialize_error_patterns(self) -> Dict:
        """初始化错误模式库"""
        return {
            "python": {
                "SyntaxError": {
                    "patterns": [r"SyntaxError:", r"invalid syntax"],
                    "suggestions": "Check for missing colons, parentheses, or quotes"
                },
                "IndentationError": {
                    "patterns": [r"IndentationError:", r"unexpected indent"],
                    "suggestions": "Use consistent indentation (4 spaces recommended)"
                },
                "NameError": {
                    "patterns": [r"NameError:", r"name '.*' is not defined"],
                    "suggestions": "Check variable name spelling and scope"
                },
                "TypeError": {
                    "patterns": [r"TypeError:", r"unsupported operand"],
                    "suggestions": "Check data types of operands"
                },
                "AttributeError": {
                    "patterns": [r"AttributeError:", r"has no attribute"],
                    "suggestions": "Check if attribute exists on the object"
                },
                "KeyError": {
                    "patterns": [r"KeyError:", r"Key '.*'"],
                    "suggestions": "Use .get() method or check if key exists"
                },
                "IndexError": {
                    "patterns": [r"IndexError:", r"list index out of range"],
                    "suggestions": "Check list bounds before accessing"
                },
                "ImportError": {
                    "patterns": [r"ImportError:", r"No module named"],
                    "suggestions": "Install missing module or check import path"
                }
            },
            "javascript": {
                "ReferenceError": {
                    "patterns": [r"ReferenceError:", r"is not defined"],
                    "suggestions": "Check variable declaration"
                },
                "TypeError": {
                    "patterns": [r"TypeError:", r"is not a function"],
                    "suggestions": "Check object type and method availability"
                },
                "SyntaxError": {
                    "patterns": [r"SyntaxError:"],
                    "suggestions": "Check for missing brackets or semicolons"
                }
            }
        }

    async def think(self, context: Dict) -> str:
        """思考过程 - 分析错误和调试策略"""
        error = context.get("error", "")
        stack_trace = context.get("stack_trace", "")
        code = context.get("code", "")

        if self.llm_provider:
            prompt = f"""
            As a senior debugger, analyze the following error and provide debugging guidance:

            Error: {error}

            Stack Trace:
            ```
            {stack_trace}
            ```

            Provide:
            1. Root cause analysis
            2. Step-by-step debugging approach
            3. Potential fixes
            """
            try:
                response = await self.llm_provider(prompt)
                return response
            except Exception as e:
                return f"Debug analysis: {str(e)}"

        return self._basic_debug_analysis(error, stack_trace)

    def _basic_debug_analysis(self, error: str, stack_trace: str) -> str:
        """基础调试分析"""
        error_type = self._identify_error_type(error)

        return f"""
        Error Analysis:
        - Type: {error_type}
        - Likely cause: {self._get_error_cause(error_type, error)}
        - Suggested fix: {self._get_error_suggestion(error_type)}
        """

    async def process_task(self, task: Dict) -> Dict:
        """
        处理调试任务

        Args:
            task: 任务描述

        Returns:
            调试结果
        """
        await self.update_status(AgentStatus.WORKING, "Debugging")
        self.current_task = task.get("task_id")

        input_data = task.get("input_data", {})
        error = input_data.get("error", task.get("description", ""))
        code = input_data.get("code", "")
        stack_trace = input_data.get("stack_trace", "")
        language = input_data.get("language", "python")

        try:
            result = await self.debug(
                error=error,
                code=code,
                stack_trace=stack_trace,
                language=language
            )

            await self.update_status(AgentStatus.SUCCESS, "Debug completed")
            self.metrics["tasks_completed"] += 1

            return result

        except Exception as e:
            await self.update_status(AgentStatus.FAILED, str(e))
            self.metrics["tasks_failed"] += 1
            return {"error": str(e)}

    async def debug(
        self,
        error: str,
        code: Optional[str] = None,
        stack_trace: Optional[str] = None,
        language: str = "python"
    ) -> Dict:
        """
        调试代码

        Args:
            error: 错误信息
            code: 相关代码
            stack_trace: 堆栈跟踪
            language: 编程语言

        Returns:
            调试结果
        """
        # 分析错误
        error_type = self._identify_error_type(error)
        error_info = self._classify_error(error, language)

        # 定位问题
        bug_info = await self.locate_bug(
            error=error,
            code=code,
            stack_trace=stack_trace,
            language=language
        )

        # 生成修复
        fix = self._generate_fix(code, bug_info, language)

        return {
            "status": "success",
            "error_analysis": {
                "type": error_type,
                "category": error_info.get("category", "unknown"),
                "severity": error_info.get("severity", "medium")
            },
            "bug": {
                "type": bug_info.bug_type,
                "message": bug_info.message,
                "cause": bug_info.cause,
                "line": bug_info.line,
                "suggestion": bug_info.suggestion
            },
            "fix": fix,
            "debug_steps": self._suggest_debug_steps(bug_info)
        }

    def _identify_error_type(self, error: str) -> str:
        """识别错误类型"""
        error_lower = error.lower()

        if "syntax" in error_lower:
            return "SyntaxError"
        elif "indentation" in error_lower:
            return "IndentationError"
        elif "name" in error_lower:
            return "NameError"
        elif "type" in error_lower:
            return "TypeError"
        elif "attribute" in error_lower:
            return "AttributeError"
        elif "key" in error_lower:
            return "KeyError"
        elif "index" in error_lower:
            return "IndexError"
        elif "import" in error_lower:
            return "ImportError"
        elif "reference" in error_lower:
            return "ReferenceError"
        elif "timeout" in error_lower:
            return "TimeoutError"
        elif "connection" in error_lower:
            return "ConnectionError"
        else:
            return "UnknownError"

    def _classify_error(self, error: str, language: str) -> Dict:
        """分类错误"""
        error_type = self._identify_error_type(error)

        # 严重性分类
        severity_map = {
            "SyntaxError": "high",
            "IndentationError": "high",
            "ImportError": "medium",
            "NameError": "high",
            "ReferenceError": "high",
            "TypeError": "medium",
            "AttributeError": "medium",
            "KeyError": "low",
            "IndexError": "low"
        }

        # 类别分类
        category_map = {
            "SyntaxError": "syntax",
            "IndentationError": "syntax",
            "NameError": "reference",
            "ReferenceError": "reference",
            "TypeError": "type",
            "AttributeError": "attribute",
            "KeyError": "data",
            "IndexError": "data",
            "ImportError": "dependency"
        }

        return {
            "severity": severity_map.get(error_type, "medium"),
            "category": category_map.get(error_type, "unknown")
        }

    async def locate_bug(
        self,
        error: str,
        code: Optional[str],
        stack_trace: Optional[str],
        language: str
    ) -> BugInfo:
        """定位Bug"""
        error_type = self._identify_error_type(error)

        # 从堆栈跟踪提取行号
        line_num = self._extract_line_from_stack(stack_trace, language)

        # 分析原因
        cause = self._get_error_cause(error_type, error)
        suggestion = self._get_error_suggestion(error_type)

        # 如果有代码，尝试精确定位
        if code and line_num:
            specific_cause = self._analyze_code_at_line(code, line_num, error_type)
            if specific_cause:
                cause = specific_cause

        return BugInfo(
            bug_type=error_type,
            severity=self._classify_error(error, language)["severity"],
            line=line_num,
            message=error,
            cause=cause,
            suggestion=suggestion,
            stack_trace=stack_trace
        )

    def _extract_line_from_stack(self, stack_trace: Optional[str], language: str) -> Optional[int]:
        """从堆栈跟踪提取行号"""
        if not stack_trace:
            return None

        # Python格式
        python_match = re.search(r'File ".*", line (\d+)', stack_trace)
        if python_match:
            return int(python_match.group(1))

        # JavaScript格式
        js_match = re.search(r':(\d+):\d+', stack_trace)
        if js_match:
            return int(js_match.group(1))

        return None

    def _analyze_code_at_line(
        self,
        code: str,
        line_num: int,
        error_type: str
    ) -> Optional[str]:
        """分析特定行的代码"""
        lines = code.split('\n')
        if 0 < line_num <= len(lines):
            line_content = lines[line_num - 1]

            if error_type == "NameError":
                match = re.search(r"name '(\w+)' is not defined", line_content)
                if match:
                    return f"Variable '{match.group(1)}' is used before being defined"

            elif error_type == "TypeError":
                return f"Type mismatch in expression: {line_content.strip()}"

            elif error_type == "IndexError":
                return "Array index is out of bounds"

        return None

    def _get_error_cause(self, error_type: str, error: str) -> str:
        """获取错误原因"""
        causes = {
            "SyntaxError": "The code contains a syntax error that prevents it from being parsed",
            "IndentationError": "Inconsistent or incorrect indentation",
            "NameError": "A variable or function name is referenced before definition",
            "TypeError": "An operation is performed on incompatible types",
            "AttributeError": "An attribute or method is accessed that doesn't exist",
            "KeyError": "A dictionary key is accessed that doesn't exist",
            "IndexError": "A list index is accessed that is out of range",
            "ImportError": "A module cannot be imported"
        }

        return causes.get(error_type, "Unknown error occurred")

    def _get_error_suggestion(self, error_type: str) -> str:
        """获取错误建议"""
        suggestions = {
            "SyntaxError": "Review the syntax around the error location. Check for missing brackets, quotes, or colons.",
            "IndentationError": "Use consistent indentation (4 spaces for Python). Check for mixed tabs and spaces.",
            "NameError": "Define the variable before use, or check for typos in the name.",
            "TypeError": "Ensure both operands have compatible types. Use type conversion if needed.",
            "AttributeError": "Verify the object has the attribute. Check for typos in the attribute name.",
            "KeyError": "Use dict.get() method or check if the key exists before access.",
            "IndexError": "Check the list length before accessing. Use len() to verify bounds.",
            "ImportError": "Install the required module or verify the module path."
        }

        return suggestions.get(error_type, "Review the error message and code carefully.")

    def _generate_fix(
        self,
        code: Optional[str],
        bug_info: BugInfo,
        language: str
    ) -> Dict:
        """生成修复代码"""
        fix = {
            "before": "",
            "after": "",
            "explanation": ""
        }

        if not code:
            fix["explanation"] = "Code not provided. Please apply the suggestion manually."
            return fix

        lines = code.split('\n')

        if bug_info.line and 0 < bug_info.line <= len(lines):
            fix["before"] = lines[bug_info.line - 1]

            # 根据错误类型生成修复
            if bug_info.bug_type == "NameError":
                # 尝试找到未定义的变量并提供定义
                match = re.search(r"name '(\w+)'", bug_info.message)
                if match:
                    var_name = match.group(1)
                    fix["explanation"] = f"Define the variable '{var_name}' before using it"
                    fix["after"] = f"# Add: {var_name} = None  # or appropriate initial value"

            elif bug_info.bug_type == "KeyError":
                fix["explanation"] = "Use dict.get() method for safe access"
                fix["after"] = lines[bug_info.line - 1].replace("[", ".get(").replace("]", ", None)")

            elif bug_info.bug_type == "IndexError":
                fix["explanation"] = "Add bounds checking before list access"
                fix["after"] = f"# Check list length before accessing\nif len(your_list) > index:\n    {lines[bug_info.line - 1]}"

            else:
                fix["explanation"] = bug_info.suggestion
        else:
            fix["explanation"] = bug_info.suggestion

        return fix

    def _suggest_debug_steps(self, bug_info: BugInfo) -> List[str]:
        """建议调试步骤"""
        steps = [
            "1. Identify the error type and location",
            "2. Review the relevant code section",
            "3. Check the variable types and values",
            "4. Verify the logic flow"
        ]

        if bug_info.bug_type == "NameError":
            steps.append("5. Search for variable definition")
        elif bug_info.bug_type == "TypeError":
            steps.append("5. Add print statements to check types")
        elif bug_info.bug_type == "IndexError":
            steps.append("5. Print list length and index value")
        elif bug_info.bug_type == "ImportError":
            steps.append("5. Check package installation")

        steps.append("6. Apply the suggested fix")
        steps.append("7. Test the fix")

        return steps

    async def _handle_bug_report(self, message: Message) -> Message:
        """处理Bug报告"""
        error = message.content.get("error", "")
        code = message.content.get("code", "")
        stack_trace = message.content.get("stack_trace", "")
        language = message.content.get("language", "python")

        result = await self.debug(error, code, stack_trace, language)

        return message.create_reply(
            content={"debug_result": result},
            message_type=MessageType.FIX_APPLIED
        )

    async def _handle_task_error(self, message: Message) -> Message:
        """处理任务错误"""
        error = message.content.get("error", "")
        task_id = message.content.get("task_id", "")

        result = await self.debug(error=error)

        return message.create_reply(
            content={"task_id": task_id, "fix": result},
            message_type=MessageType.FIX_APPLIED
        )

    async def _handle_task_request(self, message: Message) -> Message:
        """处理任务请求"""
        task_data = message.content.get("task", {})
        result = await self.process_task(task_data)

        return message.create_reply(
            content={"result": result},
            message_type=MessageType.TASK_RESPONSE
        )

    async def analyze_performance_issue(
        self,
        code: str,
        profile_data: Optional[Dict] = None,
        language: str = "python"
    ) -> Dict:
        """分析性能问题"""
        issues = []

        # 常见性能问题检测
        if "for " in code and ".append" in code:
            issues.append({
                "issue": "List building in loop",
                "suggestion": "Consider using list comprehension",
                "impact": "medium"
            })

        if "while " in code:
            issues.append({
                "issue": "While loop detected",
                "suggestion": "Ensure loop has proper termination condition",
                "impact": "depends"
            })

        # 复杂度分析
        complexity = self._estimate_complexity(code)

        return {
            "performance_issues": issues,
            "estimated_complexity": complexity,
            "recommendations": [
                "Use appropriate data structures",
                "Consider caching repeated computations",
                "Profile the code to identify bottlenecks"
            ]
        }

    def _estimate_complexity(self, code: str) -> str:
        """估算代码复杂度"""
        loops = len(re.findall(r'\b(for|while)\b', code))
        conditions = len(re.findall(r'\b(if|elif|else)\b', code))

        if loops > 5 or conditions > 10:
            return "High"
        elif loops > 2 or conditions > 5:
            return "Medium"
        return "Low"
