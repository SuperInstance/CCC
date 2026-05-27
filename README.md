# CCC — Central Command Console

A unified dashboard for monitoring and controlling agent fleets. Built with Python dataclasses, type hints, and zero external dependencies beyond `pytest` for testing.

## Install

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from ccc import Console
from ccc.models import AgentStatus

# Create the console
console = Console()

# Register fleet agents
console.register_agent("oracle1", role="keeper", model="glm-5.1")
console.register_agent("forge1", role="builder", host="node-1")
console.register_agent("jetson1", role="edge", model="jetson-orin")

# Bring agents online
console.update_status("oracle1", AgentStatus.ONLINE)
console.update_status("forge1", AgentStatus.BUSY)

# Create and assign tasks
task = console.create_task("build-artifact", agent_name_or_id="forge1", priority=5)
console.start_task(task.id)
console.complete_task(task.id)

# Report health metrics (triggers alerts on thresholds)
console.report_metric("oracle1", "cpu", 45.0, "%", warning=70.0, critical=90.0)
console.report_metric("forge1", "cpu", 95.0, "%", warning=70.0, critical=90.0)

# Execute CLI commands
result = console.execute("status")
print(result.output)
# ═══ Fleet Status ═══
#   Agents: 3 total  (1 online, 1 busy, 0 error, 1 offline)
#   Tasks:  1 total  (0 pending, 0 running, 1 done, 0 failed)
#   Metrics: 2 recorded

# Render formatted tables
print(console.render_agents())
# Name       Status   Role       Model       Host
# ─────────────────────────────────────────────────
# oracle1    online   keeper     glm-5.1
# forge1     busy     builder                node-1
# jetson1    offline  edge       jetson-orin
```

## Architecture

```
ccc/
├── __init__.py       # Public API
├── models.py         # Dataclasses: Agent, Task, HealthMetric
├── console.py        # Console — main entry point
├── dashboard.py      # Dashboard — fleet state store with queries
├── command.py        # CommandParser — CLI-style command interpreter
├── alert.py          # AlertManager — severity, escalation, notifications
└── display.py        # DisplayFormatter — ASCII/ANSI tables and sparklines
```

### Console

The main entry point. Wires together dashboard, alerts, commands, and display.

```python
from ccc import Console

c = Console()
c.register_agent("agent-1")
c.execute("status")
```

### Dashboard

In-memory store for agents, tasks, and metrics with query methods:

```python
from ccc import Dashboard

d = Dashboard()
d.add_agent(agent)
d.agents_by_status()      # → dict[AgentStatus, list[Agent]]
d.online_agents()          # → available agents
d.tasks_for_agent(id)      # → agent's tasks
d.latest_metrics(id)       # → most recent metric per type
```

### CommandParser

Interprets CLI-style commands. Built-in: `status`, `agents`, `tasks`, `alerts`, `help`.
Register custom commands:

```python
from ccc import CommandParser, Console

parser = CommandParser()

def my_handler(*, args, **kw):
    return CommandResult(command="ping", success=True, output="pong")

parser.register("ping", my_handler)
console = Console()
result = parser.execute("ping", console=console)
```

### AlertManager

Severity levels (`INFO`, `WARN`, `ERROR`, `CRITICAL`), notification channels, and auto-escalation:

```python
from ccc import AlertManager, Severity
from ccc.alert import EscalationRule

am = AlertManager()
am.add_channel("log", lambda a: print(f"[{a.severity.value}] {a.message}"))
am.add_escalation_rule(EscalationRule(
    min_severity=Severity.WARN,
    after_count=3,
    target_severity=Severity.CRITICAL,
))

am.warn("something off")  # → notified via channel
am.critical("disk full")  # → escalated if threshold hit
```

### DisplayFormatter

ASCII tables, ANSI-colored status, progress bars, and sparkline charts:

```python
from ccc import DisplayFormatter

df = DisplayFormatter(use_color=True)
print(df.render_agents(agents))
print(df.render_tasks(tasks))
print(df.render_metric_sparkline(metrics))
```

## Run Tests

```bash
python3 -m pytest tests/ -q
```

## License

MIT
