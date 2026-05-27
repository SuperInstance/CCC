"""Tests for CommandParser."""

from ccc.command import CommandParser, CommandResult
from ccc.console import Console
from ccc.models import AgentStatus


class TestCommandParser:
    def test_help(self):
        p = CommandParser()
        r = p.execute("help")
        assert r.success
        assert "status" in r.output
        assert "agents" in r.output

    def test_unknown_command(self):
        p = CommandParser()
        r = p.execute("foobar")
        assert not r.success
        assert "Unknown command" in r.error

    def test_empty_command(self):
        p = CommandParser()
        r = p.execute("")
        assert not r.success
        assert "Empty" in r.error

    def test_status_with_console(self):
        c = Console()
        c.register_agent("a1", role="keeper")
        c.update_status("a1", AgentStatus.ONLINE)
        r = c.execute("status")
        assert r.success
        assert "Agents: 1" in r.output

    def test_agents_command(self):
        c = Console()
        c.register_agent("oracle1", model="glm-5.1")
        r = c.execute("agents")
        assert r.success
        assert "oracle1" in r.output

    def test_tasks_command(self):
        c = Console()
        c.create_task("build-stuff")
        r = c.execute("tasks")
        assert r.success
        assert "build-stuff" in r.output

    def test_alerts_command(self):
        c = Console()
        c.alerts.warn("something wrong")
        r = c.execute("alerts")
        assert r.success
        assert "something wrong" in r.output

    def test_register_custom_command(self):
        p = CommandParser()

        def my_cmd(*, args, **kw):
            return CommandResult(command="ping", success=True, output="pong")

        p.register("ping", my_cmd)
        r = p.execute("ping")
        assert r.success
        assert r.output == "pong"

    def test_unregister(self):
        p = CommandParser()
        assert p.unregister("help")
        assert "help" not in p.commands

    def test_history(self):
        c = Console()
        c.execute("help")
        c.execute("status")
        assert len(c.history) == 2
