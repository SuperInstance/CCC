"""Integration tests for Console end-to-end."""

from ccc.console import Console
from ccc.models import AgentStatus, TaskStatus


class TestConsoleIntegration:
    def test_full_workflow(self):
        c = Console()

        # Register agents
        a1 = c.register_agent("oracle1", role="keeper", model="glm-5.1")
        a2 = c.register_agent("forge1", role="builder", host="node-1")
        c.update_status("oracle1", AgentStatus.ONLINE)
        c.update_status("forge1", AgentStatus.BUSY)

        # Create and run tasks
        t = c.create_task("build-ccc", agent_name_or_id="forge1", priority=5)
        assert t is not None
        c.start_task(t.id)
        t_obj = c.dashboard.get_task(t.id)
        assert t_obj.status == TaskStatus.RUNNING
        c.complete_task(t.id)
        assert t_obj.status == TaskStatus.COMPLETED

        # Report metrics
        m = c.report_metric("oracle1", "cpu", 45.0, "%", warning=70.0, critical=90.0)
        assert m is not None
        assert m.level == "ok"

        m2 = c.report_metric("forge1", "cpu", 95.0, "%", warning=70.0, critical=90.0)
        assert m2.level == "critical"

        # Check alerts were fired
        assert len(c.alerts.unacknowledged()) > 0

        # Execute commands
        r = c.execute("status")
        assert r.success
        assert "Agents: 2" in r.output

        r = c.execute("agents")
        assert r.success
        assert "oracle1" in r.output

        r = c.execute("help")
        assert r.success

    def test_remove_agent(self):
        c = Console()
        c.register_agent("temp")
        assert c.remove_agent("temp")
        assert c.dashboard.get_agent("temp") is None

    def test_fail_task_triggers_alert(self):
        c = Console()
        c.register_agent("a1")
        t = c.create_task("broken", agent_name_or_id="a1")
        c.start_task(t.id)
        c.fail_task(t.id, "segfault")
        assert any("segfault" in a.message for a in c.alerts.alerts)

    def test_render_status(self):
        c = Console()
        c.register_agent("x", role="test")
        out = c.render_status()
        assert "Central Command Console" in out

    def test_command_history(self):
        c = Console()
        c.execute("help")
        c.execute("status")
        assert len(c.history) == 2
        assert c.history[0].command == "help"
        assert c.history[1].command == "status"
