"""
Code Executor - 代码执行器
提供安全的代码执行环境，支持多种语言
"""

import asyncio
import subprocess
import tempfile
import os
import json
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
import traceback


class ExecutionStatus(Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class CodeLanguage(Enum):
    """支持的编程语言"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    C = "c"
    CPP = "cpp"
    GO = "go"
    RUST = "rust"
    RUBY = "ruby"
    PHP = "php"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    SQL = "sql"
    BASH = "bash"


@dataclass
class ExecutionResult:
    """执行结果"""
    execution_id: str
    status: ExecutionStatus
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    execution_time: float = 0.0
    memory_usage: int = 0  # KB
    output_data: Optional[Any] = None
    error: Optional[str] = None
    logs: List[Dict] = field(default_factory=list)

    def add_log(self, level: str, message: str) -> None:
        self.logs.append({
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        })

    def to_dict(self) -> Dict:
        return {
            "execution_id": self.execution_id,
            "status": self.status.value,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "return_code": self.return_code,
            "execution_time": self.execution_time,
            "memory_usage": self.memory_usage,
            "error": self.error,
            "logs": self.logs
        }


@dataclass
class ExecutionConfig:
    """执行配置"""
    timeout: int = 30  # 超时时间（秒）
    memory_limit: int = 512  # 内存限制（MB）
    cpu_limit: float = 1.0  # CPU限制
    network_enabled: bool = False  # 是否启用网络
    filesystem_enabled: bool = True  # 是否启用文件系统
    environment: Dict[str, str] = field(default_factory=dict)
    working_directory: Optional[str] = None


class CodeExecutor:
    """
    代码执行器
    提供安全的代码编译和执行环境
    """

    def __init__(self, config: Optional[ExecutionConfig] = None):
        self.config = config or ExecutionConfig()
        self._running_executions: Dict[str, asyncio.subprocess.Process] = {}
        self._execution_history: List[ExecutionResult] = []
        self._max_history = 100

        # 语言配置
        self._language_config = {
            CodeLanguage.PYTHON: {
                "extension": ".py",
                "command": ["python3"],
                "compile_needed": False
            },
            CodeLanguage.JAVASCRIPT: {
                "extension": ".js",
                "command": ["node"],
                "compile_needed": False
            },
            CodeLanguage.TYPESCRIPT: {
                "extension": ".ts",
                "command": ["npx", "ts-node"],
                "compile_needed": False
            },
            CodeLanguage.JAVA: {
                "extension": ".java",
                "command": ["java"],
                "compile_command": ["javac"],
                "compile_needed": True
            },
            CodeLanguage.C: {
                "extension": ".c",
                "command": None,  # 需要先编译
                "compile_command": ["gcc", "-o"],
                "compile_needed": True,
                "output_name": "a.out"
            },
            CodeLanguage.CPP: {
                "extension": ".cpp",
                "command": None,
                "compile_command": ["g++", "-o"],
                "compile_needed": True,
                "output_name": "a.out"
            },
            CodeLanguage.GO: {
                "extension": ".go",
                "command": ["go", "run"],
                "compile_needed": False
            },
            CodeLanguage.RUST: {
                "extension": ".rs",
                "command": ["cargo", "run"],
                "compile_needed": False
            },
            CodeLanguage.BASH: {
                "extension": ".sh",
                "command": ["bash"],
                "compile_needed": False
            }
        }

    def _get_language_config(self, language: CodeLanguage) -> Dict:
        return self._language_config.get(language, {})

    async def execute(
        self,
        code: str,
        language: CodeLanguage,
        stdin: Optional[str] = None,
        config: Optional[ExecutionConfig] = None,
        execution_id: Optional[str] = None
    ) -> ExecutionResult:
        """
        执行代码

        Args:
            code: 代码内容
            language: 编程语言
            stdin: 标准输入
            config: 执行配置
            execution_id: 执行ID

        Returns:
            执行结果
        """
        exec_id = execution_id or str(uuid.uuid4())
        exec_config = config or self.config
        lang_config = self._get_language_config(language)

        result = ExecutionResult(
            execution_id=exec_id,
            status=ExecutionStatus.RUNNING
        )

        start_time = datetime.now()
        result.add_log("info", f"Starting execution: {language.value}")

        try:
            # 创建临时文件
            with tempfile.TemporaryDirectory() as tmpdir:
                extension = lang_config.get("extension", ".txt")
                source_file = os.path.join(tmpdir, f"main{extension}")
                output_file = os.path.join(tmpdir, lang_config.get("output_name", "a.out"))

                # 写入代码
                with open(source_file, "w", encoding="utf-8") as f:
                    f.write(code)

                result.add_log("info", f"Code written to {source_file}")

                # 根据是否需要编译执行不同流程
                if lang_config.get("compile_needed", False):
                    # 编译步骤
                    compile_result = await self._compile(
                        source_file,
                        output_file,
                        lang_config,
                        exec_config,
                        tmpdir
                    )
                    result.add_log("compile", f"Compilation: {compile_result}")

                    if compile_result["return_code"] != 0:
                        result.status = ExecutionStatus.FAILED
                        result.stderr = compile_result["stderr"]
                        result.return_code = compile_result["return_code"]
                        result.error = "Compilation failed"
                        return result

                    # 执行编译后的程序
                    run_command = [output_file] if language not in [CodeLanguage.C, CodeLanguage.CPP] else []
                    exec_result = await self._run(
                        run_command if language in [CodeLanguage.C, CodeLanguage.CPP] else [output_file],
                        stdin,
                        exec_config,
                        tmpdir
                    )
                else:
                    # 直接运行
                    command = lang_config.get("command", [])
                    if language == CodeLanguage.GO:
                        command.extend([source_file])
                    else:
                        command.append(source_file)

                    exec_result = await self._run(
                        command,
                        stdin,
                        exec_config,
                        tmpdir
                    )

                # 处理结果
                result.stdout = exec_result.get("stdout", "")
                result.stderr = exec_result.get("stderr", "")
                result.return_code = exec_result.get("return_code", 0)

                if exec_result.get("return_code") == 0:
                    result.status = ExecutionStatus.SUCCESS
                    result.add_log("info", "Execution completed successfully")
                else:
                    result.status = ExecutionStatus.FAILED
                    result.error = exec_result.get("error", "Execution failed")
                    result.add_log("error", result.error)

        except asyncio.TimeoutError:
            result.status = ExecutionStatus.TIMEOUT
            result.error = "Execution timeout"
            result.add_log("error", "Execution timed out")
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error = str(e)
            result.stderr = traceback.format_exc()
            result.add_log("error", str(e))

        finally:
            result.execution_time = (datetime.now() - start_time).total_seconds()

            # 清理正在运行的进程
            if exec_id in self._running_executions:
                proc = self._running_executions.pop(exec_id)
                try:
                    proc.kill()
                except:
                    pass

            # 添加到历史
            self._execution_history.append(result)
            if len(self._execution_history) > self._max_history:
                self._execution_history = self._execution_history[-self._max_history:]

        return result

    async def _compile(
        self,
        source_file: str,
        output_file: str,
        lang_config: Dict,
        config: ExecutionConfig,
        cwd: str
    ) -> Dict:
        """编译代码"""
        compile_cmd = lang_config.get("compile_command", [])
        if compile_cmd and lang_config.get("output_name"):
            compile_cmd.extend([source_file, "-o", output_file])
        else:
            compile_cmd.append(source_file)

        try:
            proc = await asyncio.create_subprocess_exec(
                *compile_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=config.timeout
            )
            return {
                "return_code": proc.returncode,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else ""
            }
        except asyncio.TimeoutError:
            return {"return_code": -1, "stdout": "", "stderr": "Compilation timeout"}
        except Exception as e:
            return {"return_code": -1, "stdout": "", "stderr": str(e)}

    async def _run(
        self,
        command: List[str],
        stdin: Optional[str],
        config: ExecutionConfig,
        cwd: str
    ) -> Dict:
        """运行程序"""
        try:
            proc = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE if stdin else asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env={**os.environ, **config.environment}
            )

            self._running_executions[proc.pid] = proc

            if stdin:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(input=stdin.encode()),
                    timeout=config.timeout
                )
            else:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=config.timeout
                )

            return {
                "return_code": proc.returncode,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else ""
            }
        except asyncio.TimeoutError:
            return {"return_code": -1, "stdout": "", "stderr": "Execution timeout", "error": "Timeout"}
        except Exception as e:
            return {"return_code": -1, "stdout": "", "stderr": str(e), "error": str(e)}

    async def execute_test(
        self,
        code: str,
        language: CodeLanguage,
        test_cases: List[Dict]
    ) -> Dict:
        """
        执行测试用例

        Args:
            code: 代码内容
            language: 编程语言
            test_cases: 测试用例列表 [{"input": "...", "expected": "..."}]

        Returns:
            测试结果
        """
        results = []

        for i, test_case in enumerate(test_cases):
            result = await self.execute(
                code=code,
                language=language,
                stdin=test_case.get("input")
            )

            test_result = {
                "test_case": i + 1,
                "input": test_case.get("input"),
                "expected": test_case.get("expected"),
                "actual": result.stdout.strip(),
                "passed": result.stdout.strip() == str(test_case.get("expected")).strip(),
                "execution_result": result.to_dict()
            }
            results.append(test_result)

        passed = sum(1 for r in results if r["passed"])
        total = len(results)

        return {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total > 0 else 0,
            "results": results
        }

    def cancel_execution(self, execution_id: str) -> bool:
        """取消执行"""
        if execution_id in self._running_executions:
            proc = self._running_executions[execution_id]
            proc.kill()
            return True
        return False

    def get_history(self, limit: int = 50) -> List[ExecutionResult]:
        """获取执行历史"""
        return self._execution_history[-limit:]

    def get_stats(self) -> Dict:
        """获取执行统计"""
        total = len(self._execution_history)
        if total == 0:
            return {
                "total_executions": 0,
                "success_rate": 0,
                "avg_execution_time": 0
            }

        success = sum(1 for r in self._execution_history if r.status == ExecutionStatus.SUCCESS)
        total_time = sum(r.execution_time for r in self._execution_history)

        return {
            "total_executions": total,
            "success_count": success,
            "failed_count": total - success,
            "success_rate": success / total,
            "avg_execution_time": total_time / total,
            "running_executions": len(self._running_executions)
        }
