from typing import Any

from app.terminal.executor import CommandExecutor
from app.terminal.safety import is_potentially_dangerous
from app.tools.base import Tool


class RunCommandTool(Tool):
    def __init__(self, executor: CommandExecutor) -> None:
        self._executor = executor

    @property
    def name(self) -> str:
        return "run_command"

    @property
    def description(self) -> str:
        return (
            "Run a shell command in the workspace directory. Potentially "
            "destructive commands (delete, format, disk operations, "
            "registry changes) are blocked unless confirm=true is "
            "explicitly passed, which should only happen after the user "
            "has clearly approved the specific command."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute.",
                },
                "confirm": {
                    "type": "boolean",
                    "description": (
                        "Set to true only if the user has explicitly "
                        "approved this specific potentially destructive "
                        "command in this conversation."
                    ),
                },
            },
            "required": ["command"],
        }

    async def execute(self, command: str, confirm: bool = False, **kwargs: Any) -> str:
        if is_potentially_dangerous(command) and not confirm:
            return (
                f"BLOCKED: The command '{command}' was flagged as "
                "potentially destructive and requires explicit user "
                "confirmation before it can run. Ask the user to "
                "confirm this exact command before retrying with "
                "confirm=true."
            )

        result = await self._executor.run(command)

        output_parts = [
            f"Exit code: {result.exit_code}",
            f"Duration: {result.duration_seconds}s",
        ]
        if result.timed_out:
            output_parts.append("WARNING: command timed out and was killed")
        if result.stdout:
            output_parts.append(f"stdout:\n{result.stdout}")
        if result.stderr:
            output_parts.append(f"stderr:\n{result.stderr}")

        return "\n".join(output_parts)