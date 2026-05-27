"""Tests for DisplayFormatter."""

from datetime import datetime

from ccc.display import DisplayFormatter
from ccc.models import Agent, AgentStatus, Task, TaskStatus, HealthMetric
from ccc.alert import Alert, Severity
from ccc.dashboard import Dashboard


class TestDisplayAgents:
    def test_no_agents(self):
        df = DisplayFormatter(use_color=False)
        assert df.render_agents([]) == "No agents registered."

    def test_renders_table(self):
        df = DisplayFormatter(use_color=False)
        agents = [
            Agent(name="oracle1", status=AgentStatus.ONLINE, role="keeper", model="glm-5.1"),
            Agent(name="forge1", status=AgentStatus.BUSY, role="builder", host="node-1"),
        ]
        out = df.render_agents(agents)
        assert "oracle1" in out
        assert "forge1" in out
        assert "online" in out
        assert "busy" in out

    def test_with_color(self):
        df = DisplayFormatter(use_color=True)
        agents = [Agent(name="a", status=AgentStatus.ONLINE)]
        out = df.render_agents(agents)
        assert "\033[" in out  # has ANSI codes


class TestDisplayTasks:
    def test_no_tasks(self):
        df = DisplayFormatter(use_color=False)
        assert df.render_tasks([]) == "No tasks."

    def test_renders_tasks(self):
        df = DisplayFormatter(use_color=False)
        tasks = [Task(name="build", status=TaskStatus.RUNNING, progress=55.0)]
        out = df.render_tasks(tasks)
        assert "build" in out
        assert "55%" in out


class TestDisplayAlerts:
    def test_no_alerts(self):
        df = DisplayFormatter(use_color=False)
        assert df.render_alerts([]) == "No alerts."

    def test_renders_alerts(self):
        df = DisplayFormatter(use_color=False)
        alerts = [
            Alert(message="disk full", severity=Severity.ERROR, id=1, timestamp=datetime.now()),
        ]
        out = df.render_alerts(alerts)
        assert "disk full" in out


class TestDisplayDashboard:
    def test_renders_dashboard(self):
        df = DisplayFormatter(use_color=False)
        d = Dashboard()
        d.add_agent(Agent(name="a", status=AgentStatus.ONLINE))
        d.add_task(Task(name="t1", status=TaskStatus.RUNNING))
        out = df.render_dashboard(d)
        assert "Central Command Console" in out
        assert "Agents" in out


class TestDisplaySparkline:
    def test_no_data(self):
        df = DisplayFormatter()
        assert df.render_metric_sparkline([]) == "No data."

    def test_renders_sparkline(self):
        df = DisplayFormatter()
        metrics = [HealthMetric(agent_id="a", name="cpu", value=float(i * 10)) for i in range(8)]
        out = df.render_metric_sparkline(metrics)
        assert "cpu" in out
        assert "▁" in out or "█" in out  # has sparkline chars
