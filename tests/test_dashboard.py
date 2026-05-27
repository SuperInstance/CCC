"""Tests for Dashboard."""

from ccc.models import Agent, AgentStatus, Task, TaskStatus, HealthMetric
from ccc.dashboard import Dashboard


class TestDashboardAgents:
    def test_add_and_get_by_id(self):
        d = Dashboard()
        a = Agent(name="oracle1")
        d.add_agent(a)
        assert d.get_agent(a.id) is a

    def test_get_by_name(self):
        d = Dashboard()
        a = Agent(name="forge1")
        d.add_agent(a)
        assert d.get_agent("forge1") is a

    def test_remove_agent(self):
        d = Dashboard()
        a = Agent(name="x")
        d.add_agent(a)
        assert d.remove_agent(a.id)
        assert d.get_agent(a.id) is None

    def test_agents_list(self):
        d = Dashboard()
        d.add_agent(Agent(name="a"))
        d.add_agent(Agent(name="b"))
        assert len(d.agents) == 2

    def test_online_agents(self):
        d = Dashboard()
        d.add_agent(Agent(name="up", status=AgentStatus.ONLINE))
        d.add_agent(Agent(name="down", status=AgentStatus.OFFLINE))
        assert len(d.online_agents()) == 1

    def test_agents_by_status(self):
        d = Dashboard()
        d.add_agent(Agent(name="a", status=AgentStatus.ONLINE))
        d.add_agent(Agent(name="b", status=AgentStatus.ONLINE))
        d.add_agent(Agent(name="c", status=AgentStatus.ERROR))
        by = d.agents_by_status()
        assert len(by[AgentStatus.ONLINE]) == 2
        assert len(by[AgentStatus.ERROR]) == 1


class TestDashboardTasks:
    def test_add_and_get(self):
        d = Dashboard()
        t = Task(name="job")
        d.add_task(t)
        assert d.get_task(t.id) is t

    def test_tasks_for_agent(self):
        d = Dashboard()
        t1 = Task(name="a", agent_id="ag1")
        t2 = Task(name="b", agent_id="ag2")
        d.add_task(t1)
        d.add_task(t2)
        assert len(d.tasks_for_agent("ag1")) == 1

    def test_pending_tasks(self):
        d = Dashboard()
        d.add_task(Task(name="p", status=TaskStatus.PENDING))
        d.add_task(Task(name="r", status=TaskStatus.RUNNING))
        assert len(d.pending_tasks()) == 1

    def test_remove_task(self):
        d = Dashboard()
        t = Task(name="x")
        d.add_task(t)
        assert d.remove_task(t.id)
        assert d.get_task(t.id) is None


class TestDashboardMetrics:
    def test_add_metric(self):
        d = Dashboard()
        m = HealthMetric(agent_id="a", name="cpu", value=50.0)
        d.add_metric(m)
        assert len(d.metrics) == 1

    def test_max_metrics_trimming(self):
        d = Dashboard(max_metrics=5)
        for i in range(10):
            d.add_metric(HealthMetric(agent_id="a", name="cpu", value=float(i)))
        assert len(d.metrics) == 5

    def test_latest_metrics(self):
        d = Dashboard()
        d.add_metric(HealthMetric(agent_id="a", name="cpu", value=10.0))
        d.add_metric(HealthMetric(agent_id="a", name="mem", value=20.0))
        d.add_metric(HealthMetric(agent_id="a", name="cpu", value=90.0))
        latest = d.latest_metrics("a")
        assert latest["cpu"].value == 90.0
        assert latest["mem"].value == 20.0


class TestDashboardSummary:
    def test_summary(self):
        d = Dashboard()
        d.add_agent(Agent(name="a", status=AgentStatus.ONLINE))
        d.add_agent(Agent(name="b", status=AgentStatus.ERROR))
        d.add_task(Task(name="t1", status=TaskStatus.RUNNING))
        d.add_task(Task(name="t2", status=TaskStatus.COMPLETED))
        s = d.summary()
        assert s["agents"]["total"] == 2
        assert s["agents"]["online"] == 1
        assert s["tasks"]["completed"] == 1
