import asyncio
import subprocess
import time
from dataclasses import dataclass


@dataclass
class CommandResult:
    command: str
    stdout: str
    stderr: str
    exit_code: int
    duration_seconds: float
    timed_out: bool


class CommandExecutor:
    def __init__(self, working_directory: str, timeout_seconds: float = 30.0) -> None:
        self._working_directory = working_directory
        self._timeout_seconds = timeout_seconds

    async def run(self, command: str) -> CommandResult:
        return await asyncio.to_thread(self._run_sync, command)

    def _run_sync(self, command: str) -> CommandResult:
        start_time = time.monotonic()
        timed_out = False

        try:
            completed = subprocess.run(
                command,
                shell=True,
                cwd=self._working_directory,
                capture_output=True,
                timeout=self._timeout_seconds,
            )
            stdout = completed.stdout.decode(errors="replace")
            stderr = completed.stderr.decode(errors="replace")
            exit_code = completed.returncode
        except subprocess.TimeoutExpired as error:
            timed_out = True
            stdout = (error.stdout or b"").decode(errors="replace")
            stderr = (error.stderr or b"").decode(errors="replace")
            exit_code = -1

        duration = time.monotonic() - start_time

        return CommandResult(
            command=command,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            duration_seconds=round(duration, 2),
            timed_out=timed_out,
        )