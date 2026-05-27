"""Core data models for CCC."""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


class AgentStatus(str, enum.Enum):
    """Possible states for a fleet agent."""

    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"
    IDLE = "idle"
    STARTING = "starting"
    STOPPING = "stopping"


class TaskStatus(str, enum.Enum):
    """Possible states for a task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Agent:
    """Represents a single agent in the fleet."""

    name: str
    status: AgentStatus = AgentStatus.OFFLINE
    role: str = ""
    host: str = ""
    model: str = ""
    capabilities: list[str] = field(default_factory=list)
    last_seen: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    def is_available(self) -> bool:
        return self.status in (AgentStatus.ONLINE, AgentStatus.IDLE)

    def touch(self) -> None:
        self.last_seen = datetime.now()


@dataclass
class Task:
    """A unit of work assigned to an agent."""

    name: str
    agent_id: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0
    progress: float = 0.0
    created: datetime = field(default_factory=datetime.now)
    started: datetime | None = None
    finished: datetime | None = None
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    def duration_seconds(self) -> float | None:
        if self.started is None:
            return None
        end = self.finished or datetime.now()
        return (end - self.started).total_seconds()


@dataclass
class HealthMetric:
    """A health metric reading from an agent."""

    agent_id: str
    name: str
    value: float
    unit: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    warning_threshold: float | None = None
    critical_threshold: float | None = None

    @property
    def level(self) -> str:
        if self.critical_threshold is not None and self.value >= self.critical_threshold:
            return "critical"
        if self.warning_threshold is not None and self.value >= self.warning_threshold:
            return "warning"
        return "ok"
