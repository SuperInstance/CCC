"""Dashboard — panels for agents, tasks, and health metrics."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from ccc.models import Agent, Task, TaskStatus, AgentStatus, HealthMetric


class Dashboard:
    """In-memory dashboard holding fleet state.

    Attributes:
        agents: dict mapping agent ID → Agent
        tasks: dict mapping task ID → Task
        metrics: list of recent health metric readings
    """

    def __init__(self, max_metrics: int = 1000) -> None:
        self._agents: dict[str, Agent] = {}
        self._agent_name_index: dict[str, str] = {}  # name → id
        self._tasks: dict[str, Task] = {}
        self._metrics: list[HealthMetric] = []
        self._max_metrics = max_metrics

    # ── Agent operations ──────────────────────────────────────────

    def add_agent(self, agent: Agent) -> None:
        self._agents[agent.id] = agent
        self._agent_name_index[agent.name] = agent.id

    def remove_agent(self, agent_id: str) -> bool:
        agent = self._agents.pop(agent_id, None)
        if agent is None:
            return False
        self._agent_name_index.pop(agent.name, None)
        return True

    def get_agent(self, name_or_id: str) -> Agent | None:
        if name_or_id in self._agents:
            return self._agents[name_or_id]
        aid = self._agent_name_index.get(name_or_id)
        if aid is not None:
            return self._agents.get(aid)
        return None

    @property
    def agents(self) -> list[Agent]:
        return list(self._agents.values())

    def agents_by_status(self) -> dict[AgentStatus, list[Agent]]:
        result: dict[AgentStatus, list[Agent]] = defaultdict(list)
        for a in self._agents.values():
            result[a.status].append(a)
        return dict(result)

    def online_agents(self) -> list[Agent]:
        return [a for a in self._agents.values() if a.is_available()]

    # ── Task operations ───────────────────────────────────────────

    def add_task(self, task: Task) -> None:
        self._tasks[task.id] = task

    def get_task(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def remove_task(self, task_id: str) -> bool:
        return self._tasks.pop(task_id, None) is not None

    @property
    def tasks(self) -> list[Task]:
        return list(self._tasks.values())

    def tasks_by_status(self) -> dict[TaskStatus, list[Task]]:
        result: dict[TaskStatus, list[Task]] = defaultdict(list)
        for t in self._tasks.values():
            result[t.status].append(t)
        return dict(result)

    def tasks_for_agent(self, agent_id: str) -> list[Task]:
        return [t for t in self._tasks.values() if t.agent_id == agent_id]

    def pending_tasks(self) -> list[Task]:
        return [t for t in self._tasks.values() if t.status == TaskStatus.PENDING]

    # ── Metrics ───────────────────────────────────────────────────

    def add_metric(self, metric: HealthMetric) -> None:
        self._metrics.append(metric)
        if len(self._metrics) > self._max_metrics:
            self._metrics = self._metrics[-self._max_metrics:]

    @property
    def metrics(self) -> list[HealthMetric]:
        return list(self._metrics)

    def latest_metrics(self, agent_id: str) -> dict[str, HealthMetric]:
        """Return the most recent metric of each type for an agent."""
        latest: dict[str, HealthMetric] = {}
        for m in self._metrics:
            if m.agent_id == agent_id:
                if m.name not in latest or m.timestamp > latest[m.name].timestamp:
                    latest[m.name] = m
        return latest

    def metrics_for_agent(self, agent_id: str) -> list[HealthMetric]:
        return [m for m in self._metrics if m.agent_id == agent_id]

    # ── Summary ───────────────────────────────────────────────────

    def summary(self) -> dict[str, Any]:
        by_status = self.agents_by_status()
        tasks_by_status = self.tasks_by_status()
        return {
            "agents": {
                "total": len(self._agents),
                "online": len(by_status.get(AgentStatus.ONLINE, [])),
                "busy": len(by_status.get(AgentStatus.BUSY, [])),
                "error": len(by_status.get(AgentStatus.ERROR, [])),
                "offline": len(by_status.get(AgentStatus.OFFLINE, [])),
            },
            "tasks": {
                "total": len(self._tasks),
                "pending": len(tasks_by_status.get(TaskStatus.PENDING, [])),
                "running": len(tasks_by_status.get(TaskStatus.RUNNING, [])),
                "completed": len(tasks_by_status.get(TaskStatus.COMPLETED, [])),
                "failed": len(tasks_by_status.get(TaskStatus.FAILED, [])),
            },
            "metrics": len(self._metrics),
        }
