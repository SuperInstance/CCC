"""Console — main entry point for fleet monitoring and control."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ccc.models import Agent, AgentStatus, Task, TaskStatus, HealthMetric
from ccc.dashboard import Dashboard
from ccc.command import CommandParser, CommandResult
from ccc.alert import AlertManager
from ccc.display import DisplayFormatter


class Console:
    """Central Command Console — unified dashboard for agent fleets.

    Example::

        console = Console()
        console.register_agent("oracle1", role="keeper", model="glm-5.1")
        console.update_status("oracle1", AgentStatus.ONLINE)

        result = console.execute("status")
        print(result.output)
    """

    def __init__(self, name: str = "CCC") -> None:
        self.name = name
        self.dashboard = Dashboard()
        self.alerts = AlertManager()
        self.parser = CommandParser()
        self.display = DisplayFormatter()
        self._history: list[CommandResult] = []

    # ── Agent management ──────────────────────────────────────────

    def register_agent(
        self,
        name: str,
        *,
        role: str = "",
        host: str = "",
        model: str = "",
        capabilities: list[str] | None = None,
    ) -> Agent:
        """Register a new agent in the fleet."""
        agent = Agent(
            name=name,
            role=role,
            host=host,
            model=model,
            capabilities=capabilities or [],
        )
        self.dashboard.add_agent(agent)
        return agent

    def remove_agent(self, name_or_id: str) -> bool:
        """Remove an agent by name or ID."""
        agent = self.dashboard.get_agent(name_or_id)
        if agent is None:
            return False
        self.dashboard.remove_agent(agent.id)
        return True

    def update_status(self, name_or_id: str, status: AgentStatus) -> Agent | None:
        """Update an agent's status."""
        agent = self.dashboard.get_agent(name_or_id)
        if agent is None:
            return None
        agent.status = status
        agent.touch()
        if status == AgentStatus.ERROR:
            self.alerts.warn(f"Agent {agent.name} entered ERROR state")
        return agent

    # ── Task management ───────────────────────────────────────────

    def create_task(
        self,
        name: str,
        agent_name_or_id: str = "",
        priority: int = 0,
        **metadata: Any,
    ) -> Task | None:
        """Create a new task, optionally assigning it to an agent."""
        agent_id = ""
        if agent_name_or_id:
            agent = self.dashboard.get_agent(agent_name_or_id)
            if agent is None:
                return None
            agent_id = agent.id
        task = Task(name=name, agent_id=agent_id, priority=priority, metadata=metadata)
        self.dashboard.add_task(task)
        return task

    def start_task(self, task_id: str) -> bool:
        task = self.dashboard.get_task(task_id)
        if task is None:
            return False
        task.status = TaskStatus.RUNNING
        task.started = datetime.now()
        return True

    def complete_task(self, task_id: str) -> bool:
        task = self.dashboard.get_task(task_id)
        if task is None:
            return False
        task.status = TaskStatus.COMPLETED
        task.finished = datetime.now()
        return True

    def fail_task(self, task_id: str, error: str = "") -> bool:
        task = self.dashboard.get_task(task_id)
        if task is None:
            return False
        task.status = TaskStatus.FAILED
        task.finished = datetime.now()
        task.error = error
        self.alerts.error(f"Task {task.name} failed: {error}")
        return True

    # ── Health metrics ────────────────────────────────────────────

    def report_metric(
        self,
        agent_name_or_id: str,
        metric_name: str,
        value: float,
        unit: str = "",
        warning: float | None = None,
        critical: float | None = None,
    ) -> HealthMetric | None:
        agent = self.dashboard.get_agent(agent_name_or_id)
        if agent is None:
            return None
        metric = HealthMetric(
            agent_id=agent.id,
            name=metric_name,
            value=value,
            unit=unit,
            warning_threshold=warning,
            critical_threshold=critical,
        )
        self.dashboard.add_metric(metric)
        if metric.level == "critical":
            self.alerts.critical(
                f"{agent.name}/{metric_name} = {value}{unit} (critical)"
            )
        elif metric.level == "warning":
            self.alerts.warn(
                f"{agent.name}/{metric_name} = {value}{unit} (warning)"
            )
        return metric

    # ── Command execution ─────────────────────────────────────────

    def execute(self, command_line: str) -> CommandResult:
        """Parse and execute a CLI-style command."""
        result = self.parser.execute(command_line, console=self)
        self._history.append(result)
        return result

    @property
    def history(self) -> list[CommandResult]:
        return list(self._history)

    # ── Convenience display methods ───────────────────────────────

    def render_status(self) -> str:
        return self.display.render_dashboard(self.dashboard)

    def render_agents(self) -> str:
        return self.display.render_agents(self.dashboard.agents)

    def render_tasks(self) -> str:
        return self.display.render_tasks(self.dashboard.tasks)

    def render_alerts(self) -> str:
        return self.display.render_alerts(self.alerts.alerts)
