"""CommandParser — CLI-style command interpreter for fleet control."""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable


@dataclass
class CommandResult:
    """Result of executing a command."""

    command: str
    success: bool
    output: str = ""
    error: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


# Type alias for command handlers
CommandHandler = Callable[..., CommandResult]


class CommandParser:
    """Parses and executes CLI-style commands for fleet control.

    Built-in commands::

        status              — fleet overview
        agents              — list all agents
        tasks               — list all tasks
        alerts              — show recent alerts
        help                — list available commands

    You can register custom commands with :meth:`register`.

    Example::

        parser = CommandParser()
        result = parser.execute("status", console=my_console)
        print(result.output)
    """

    def __init__(self) -> None:
        self._commands: dict[str, CommandHandler] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self._commands["status"] = self._cmd_status
        self._commands["agents"] = self._cmd_agents
        self._commands["tasks"] = self._cmd_tasks
        self._commands["alerts"] = self._cmd_alerts
        self._commands["help"] = self._cmd_help

    def register(self, name: str, handler: CommandHandler) -> None:
        """Register a custom command handler."""
        self._commands[name] = handler

    def unregister(self, name: str) -> bool:
        """Remove a registered command."""
        return self._commands.pop(name, None) is not None

    @property
    def commands(self) -> list[str]:
        return sorted(self._commands.keys())

    def execute(self, command_line: str, **context: Any) -> CommandResult:
        """Parse and execute a command string.

        Args:
            command_line: Raw command string (e.g. ``"status"`` or ``"agents --filter online"``).
            **context: Keyword arguments passed to the handler (e.g. ``console=...``).

        Returns:
            A CommandResult with output or error.
        """
        command_line = command_line.strip()
        if not command_line:
            return CommandResult(command="", success=False, error="Empty command")

        try:
            parts = shlex.split(command_line)
        except ValueError as exc:
            return CommandResult(
                command=command_line, success=False, error=f"Parse error: {exc}"
            )

        cmd_name = parts[0].lower()
        args = parts[1:]

        handler = self._commands.get(cmd_name)
        if handler is None:
            available = ", ".join(self._commands.keys())
            return CommandResult(
                command=cmd_name,
                success=False,
                error=f"Unknown command: {cmd_name}. Available: {available}",
            )

        try:
            return handler(args=args, **context)
        except Exception as exc:
            return CommandResult(
                command=cmd_name, success=False, error=f"Command error: {exc}"
            )

    # ── Default command implementations ───────────────────────────

    def _cmd_status(self, *, args: list[str], console: Any = None, **_kw: Any) -> CommandResult:
        if console is None:
            return CommandResult(command="status", success=False, error="No console context")
        summary = console.dashboard.summary()
        lines = [
            "═══ Fleet Status ═══",
            f"  Agents: {summary['agents']['total']} total  "
            f"({summary['agents']['online']} online, "
            f"{summary['agents']['busy']} busy, "
            f"{summary['agents']['error']} error, "
            f"{summary['agents']['offline']} offline)",
            f"  Tasks:  {summary['tasks']['total']} total  "
            f"({summary['tasks']['pending']} pending, "
            f"{summary['tasks']['running']} running, "
            f"{summary['tasks']['completed']} done, "
            f"{summary['tasks']['failed']} failed)",
            f"  Metrics: {summary['metrics']} recorded",
        ]
        return CommandResult(command="status", success=True, output="\n".join(lines))

    def _cmd_agents(self, *, args: list[str], console: Any = None, **_kw: Any) -> CommandResult:
        if console is None:
            return CommandResult(command="agents", success=False, error="No console context")
        return CommandResult(
            command="agents", success=True, output=console.render_agents()
        )

    def _cmd_tasks(self, *, args: list[str], console: Any = None, **_kw: Any) -> CommandResult:
        if console is None:
            return CommandResult(command="tasks", success=False, error="No console context")
        return CommandResult(
            command="tasks", success=True, output=console.render_tasks()
        )

    def _cmd_alerts(self, *, args: list[str], console: Any = None, **_kw: Any) -> CommandResult:
        if console is None:
            return CommandResult(command="alerts", success=False, error="No console context")
        return CommandResult(
            command="alerts", success=True, output=console.render_alerts()
        )

    def _cmd_help(self, *, args: list[str], **_kw: Any) -> CommandResult:
        lines = ["Available commands:"]
        for name in sorted(self._commands.keys()):
            lines.append(f"  {name}")
        return CommandResult(command="help", success=True, output="\n".join(lines))
