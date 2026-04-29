"""
Reviewer Agent - 评审员Agent
负责代码审查、质量评估和改进建议
"""

from typing import Dict, List, Optional, Any, Tuple
import re
from dataclasses import dataclass
from ..core.agent import Agent, AgentRole, AgentStatus, AgentCapability
from ..core.message import Message, MessageType


@dataclass
class CodeIssue:
    """代码问题"""
    severity: str  # error, warning, info
    category: str  # style, security, performance, bug, maintainability
    line: int
    message: str
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None


class ReviewerAgent(Agent):
    """
    评审员Agent
    专注于代码质量和最佳实践审查
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        llm_provider: Optional[callable] = None
    ):
        capabilities = AgentCapability(
            languages=["python", "javascript", "typescript", "java", "go", "rust"],
            frameworks=["react", "vue", "fastapi", "django", "spring"],
            expertise=["code_review", "security", "performance", "best_practices"],
            max_concurrent_tasks=3
        )
        super().__init__(agent_id, name, AgentRole.REVIEWER, capabilities, llm_provider)

        # 审查规则
        self.review_rules = self._initialize_review_rules()

        # 最佳实践检查器
        self.best_practices = {
            "python": self._python_best_practices,
            "javascript": self._javascript_best_practices
        }

        # 注册消息处理器
        self.register_handler(MessageType.CODE_REVIEW.value, self._handle_code_review)
        self.register_handler(MessageType.TASK_REQUEST.value, self._handle_task_request)

    def _initialize_review_rules(self) -> Dict:
        """初始化审查规则"""
        return {
            "security": [
                {"pattern": r"password\s*=\s*['\"][^'\"]{0,20}['\"]", "severity": "error", "message": "Hardcoded password detected"},
                {"pattern": r"eval\s*\(", "severity": "error", "message": "Use of eval() is a security risk"},
                {"pattern": r"exec\s*\(", "severity": "error", "message": "Use of exec() is a security risk"},
                {"pattern": r"os\.system\s*\(", "severity": "warning", "message": "Consider using subprocess module"},
                {"pattern": r"input\s*\(", "severity": "info", "message": "User input should be sanitized"}
            ],
            "style": [
                {"pattern": r"    ", "severity": "info", "message": "Use consistent indentation"},
                {"pattern": r"\r\n", "severity": "info", "message": "Inconsistent line endings"}
            ],
            "performance": [
                {"pattern": r"for .* in .*:\s+.*\.append\(", "severity": "info", "message": "Consider using list comprehension"},
                {"pattern": r"\.join\(", "severity": "info", "message": "String concatenation with join is efficient"}
            ]
        }

    async def think(self, context: Dict) -> str:
        """思考过程 - 分析代码审查需求"""
        code = context.get("code", "")
        language = context.get("language", "python")

        if self.llm_provider:
            prompt = f"""
            As a senior code reviewer, analyze the following code and provide feedback:

            Language: {language}

            ```code
            {code[:2000]}
            ```

            Provide feedback on:
            1. Code quality
            2. Potential bugs
            3. Security concerns
            4. Performance issues
            5. Best practices compliance
            """
            try:
                response = await self.llm_provider(prompt)
                return response
            except Exception as e:
                return f"Code review analysis: {str(e)}"

        return "Performing automated code review..."

    async def process_task(self, task: Dict) -> Dict:
        """
        处理代码审查任务

        Args:
            task: 任务描述

        Returns:
            审查结果
        """
        await self.update_status(AgentStatus.WORKING, "Reviewing code")
        self.current_task = task.get("task_id")

        input_data = task.get("input_data", {})
        code = input_data.get("code", task.get("description", ""))
        language = input_data.get("language", "python")

        try:
            result = await self.review_code(code, language)

            await self.update_status(AgentStatus.SUCCESS, "Review completed")
            self.metrics["tasks_completed"] += 1

            return result

        except Exception as e:
            await self.update_status(AgentStatus.FAILED, str(e))
            self.metrics["tasks_failed"] += 1
            return {"error": str(e)}

    async def review_code(
        self,
        code: str,
        language: str,
        rules: Optional[Dict] = None
    ) -> Dict:
        """
        全面审查代码

        Args:
            code: 代码内容
            language: 编程语言
            rules: 自定义审查规则

        Returns:
            审查结果
        """
        issues = []
        review_rules = rules or self.review_rules

        # 逐行检查
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            line_issues = self._check_line(line, line_num, review_rules)
            issues.extend(line_issues)

        # 安全检查
        security_issues = self._check_security(code)
        issues.extend(security_issues)

        # 风格检查
        style_issues = self._check_style(code, language)
        issues.extend(style_issues)

        # 性能检查
        performance_issues = self._check_performance(code, language)
        issues.extend(performance_issues)

        # 最佳实践检查
        if language in self.best_practices:
            bp_issues = self.best_practices[language](code)
            issues.extend(bp_issues)

        # 计算质量评分
        quality_score = self._calculate_quality_score(code, issues)

        # 生成建议
        suggestions = self._generate_suggestions(issues)

        return {
            "status": "success",
            "summary": {
                "total_lines": len(lines),
                "total_issues": len(issues),
                "errors": sum(1 for i in issues if i.severity == "error"),
                "warnings": sum(1 for i in issues if i.severity == "warning"),
                "info": sum(1 for i in issues if i.severity == "info"),
                "quality_score": quality_score
            },
            "issues": [self._issue_to_dict(i) for i in issues],
            "suggestions": suggestions,
            "security_audit": {
                "passed": all(i.severity != "error" for i in issues if i.category == "security"),
                "concerns": [self._issue_to_dict(i) for i in issues if i.category == "security"]
            }
        }

    def _check_line(self, line: str, line_num: int, rules: Dict) -> List[CodeIssue]:
        """检查单行代码"""
        issues = []

        for category, category_rules in rules.items():
            for rule in category_rules:
                if re.search(rule["pattern"], line):
                    issues.append(CodeIssue(
                        severity=rule["severity"],
                        category=category,
                        line=line_num,
                        message=rule["message"],
                        code_snippet=line.strip()
                    ))

        return issues

    def _check_security(self, code: str) -> List[CodeIssue]:
        """安全检查"""
        issues = []
        lines = code.split('\n')

        security_patterns = [
            (r"['\"][a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}['\"]", "info", "Email address found"),
            (r"api[_-]?key\s*=", "warning", "API key in code"),
            (r"secret\s*=", "warning", "Secret key in code"),
            (r"token\s*=", "info", "Token assignment found"),
            (r"sanitize|escape", "info", "Input sanitization mentioned")
        ]

        for line_num, line in enumerate(lines, 1):
            for pattern, severity, message in security_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(CodeIssue(
                        severity=severity,
                        category="security",
                        line=line_num,
                        message=message,
                        code_snippet=line.strip()
                    ))

        return issues

    def _check_style(self, code: str, language: str) -> List[CodeIssue]:
        """风格检查"""
        issues = []
        lines = code.split('\n')

        # 检查行长
        for line_num, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append(CodeIssue(
                    severity="info",
                    category="style",
                    line=line_num,
                    message=f"Line too long ({len(line)} characters)",
                    suggestion="Consider breaking long lines"
                ))

        # 语言特定的风格检查
        if language == "python":
            # 检查缺少docstring
            if not re.search(r'""".*?"""', code, re.DOTALL):
                issues.append(CodeIssue(
                    severity="info",
                    category="style",
                    line=1,
                    message="No module docstring found"
                ))

        return issues

    def _check_performance(self, code: str, language: str) -> List[CodeIssue]:
        """性能检查"""
        issues = []
        lines = code.split('\n')

        performance_patterns = [
            (r"\+ '", "warning", "String concatenation in loop", "Use list and join"),
            (r"for .* in .*:.*\+= 1", "info", "Consider using enumerate"),
            (r"\.append\(.*\+", "info", "Complex append operation")
        ]

        for line_num, line in enumerate(lines, 1):
            for pattern, severity, message, suggestion in performance_patterns:
                if re.search(pattern, line):
                    issues.append(CodeIssue(
                        severity=severity,
                        category="performance",
                        line=line_num,
                        message=message,
                        suggestion=suggestion,
                        code_snippet=line.strip()
                    ))

        return issues

    def _python_best_practices(self, code: str) -> List[CodeIssue]:
        """Python最佳实践检查"""
        issues = []
        lines = code.split('\n')

        # 检查类型提示
        if "def " in code and "->" not in code:
            issues.append(CodeIssue(
                severity="info",
                category="maintainability",
                line=1,
                message="Consider adding type hints",
                suggestion="def function(param: Type) -> ReturnType:"
            ))

        # 检查异常处理
        if "except:" in code:
            issues.append(CodeIssue(
                severity="warning",
                category="bug",
                line=1,
                message="Bare except clause found",
                suggestion="except Exception as e:"
            ))

        # 检查相对导入
        if "from ." in code:
            issues.append(CodeIssue(
                severity="info",
                category="maintainability",
                line=1,
                message="Relative import found"
            ))

        return issues

    def _javascript_best_practices(self, code: str) -> List[CodeIssue]:
        """JavaScript最佳实践检查"""
        issues = []
        lines = code.split('\n')

        # 检查var
        if re.search(r'\bvar\s+\w+', code):
            issues.append(CodeIssue(
                severity="info",
                category="maintainability",
                line=1,
                message="Consider using const or let instead of var"
            ))

        # 检查console.log
        if "console.log" in code:
            issues.append(CodeIssue(
                severity="info",
                category="maintainability",
                line=1,
                message="Debug code found",
                suggestion="Remove console.log in production"
            ))

        return issues

    def _calculate_quality_score(self, code: str, issues: List[CodeIssue]) -> float:
        """计算质量评分"""
        if not code.strip():
            return 0.0

        lines = len(code.split('\n'))
        base_score = 100.0

        # 根据问题扣分
        for issue in issues:
            if issue.severity == "error":
                base_score -= 10
            elif issue.severity == "warning":
                base_score -= 5
            else:
                base_score -= 1

        # 根据代码行数调整（长代码更容易出问题）
        if lines > 500:
            base_score *= 0.9

        return max(0.0, min(100.0, base_score))

    def _generate_suggestions(self, issues: List[CodeIssue]) -> List[str]:
        """生成改进建议"""
        suggestions = []

        # 按类别分组
        by_category = {}
        for issue in issues:
            if issue.category not in by_category:
                by_category[issue.category] = []
            by_category[issue.category].append(issue)

        # 生成建议
        for category, category_issues in by_category.items():
            if category == "security" and any(i.severity == "error" for i in category_issues):
                suggestions.append("⚠️ Address all security issues immediately before deployment")
            if category == "performance" and len(category_issues) > 2:
                suggestions.append("💡 Consider refactoring for better performance")
            if category == "style":
                suggestions.append("📝 Apply consistent code style (consider using a linter)")

        if not suggestions:
            suggestions.append("✅ Code looks good! Consider adding more tests.")

        return suggestions

    def _issue_to_dict(self, issue: CodeIssue) -> Dict:
        """将问题转换为字典"""
        return {
            "severity": issue.severity,
            "category": issue.category,
            "line": issue.line,
            "message": issue.message,
            "suggestion": issue.suggestion,
            "code_snippet": issue.code_snippet
        }

    async def _handle_code_review(self, message: Message) -> Message:
        """处理代码审查请求"""
        code = message.content.get("code", "")
        language = message.content.get("language", "python")

        result = await self.review_code(code, language)

        return message.create_reply(
            content={"review": result},
            message_type=MessageType.CODE_REVIEW
        )

    async def _handle_task_request(self, message: Message) -> Message:
        """处理任务请求"""
        task_data = message.content.get("task", {})
        result = await self.process_task(task_data)

        return message.create_reply(
            content={"result": result},
            message_type=MessageType.TASK_RESPONSE
        )

    async def compare_implementations(
        self,
        code_a: str,
        code_b: str,
        language: str
    ) -> Dict:
        """比较两个实现"""
        review_a = await self.review_code(code_a, language)
        review_b = await self.review_code(code_b, language)

        score_a = review_a["summary"]["quality_score"]
        score_b = review_b["summary"]["quality_score"]

        return {
            "implementation_a": {
                "score": score_a,
                "issues": review_a["summary"]["total_issues"]
            },
            "implementation_b": {
                "score": score_b,
                "issues": review_b["summary"]["total_issues"]
            },
            "recommendation": "Implementation A" if score_a > score_b else "Implementation B",
            "score_difference": abs(score_a - score_b)
        }
