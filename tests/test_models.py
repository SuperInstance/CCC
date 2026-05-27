"""Tests for core models."""

from datetime import datetime

from ccc.models import Agent, AgentStatus, Task, TaskStatus, HealthMetric


class TestAgent:
    def test_defaults(self):
        a = Agent(name="test")
        assert a.name == "test"
        assert a.status == AgentStatus.OFFLINE
        assert a.capabilities == []
        assert a.id  # auto-generated

    def test_is_available(self):
        assert Agent(name="a", status=AgentStatus.ONLINE).is_available()
        assert Agent(name="a", status=AgentStatus.IDLE).is_available()
        assert not Agent(name="a", status=AgentStatus.BUSY).is_available()
        assert not Agent(name="a", status=AgentStatus.OFFLINE).is_available()
        assert not Agent(name="a", status=AgentStatus.ERROR).is_available()

    def test_touch(self):
        a = Agent(name="a")
        assert a.last_seen is None
        a.touch()
        assert a.last_seen is not None
        assert isinstance(a.last_seen, datetime)


class TestTask:
    def test_defaults(self):
        t = Task(name="do-thing")
        assert t.name == "do-thing"
        assert t.status == TaskStatus.PENDING
        assert t.priority == 0
        assert t.progress == 0.0

    def test_duration(self):
        t = Task(name="x")
        assert t.duration_seconds() is None
        t.started = datetime(2026, 1, 1, 10, 0, 0)
        t.finished = datetime(2026, 1, 1, 10, 0, 30)
        assert t.duration_seconds() == 30.0


class TestHealthMetric:
    def test_level_ok(self):
        m = HealthMetric(agent_id="a", name="cpu", value=50.0)
        assert m.level == "ok"

    def test_level_warning(self):
        m = HealthMetric(agent_id="a", name="cpu", value=75.0, warning_threshold=70.0)
        assert m.level == "warning"

    def test_level_critical(self):
        m = HealthMetric(
            agent_id="a", name="cpu", value=95.0,
            warning_threshold=70.0, critical_threshold=90.0,
        )
        assert m.level == "critical"

    def test_no_thresholds(self):
        m = HealthMetric(agent_id="a", name="mem", value=999.0)
        assert m.level == "ok"
