"""DisplayFormatter — render status as ASCII/ANSI tables and charts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ccc.models import Agent, AgentStatus, Task, TaskStatus, HealthMetric
from ccc.alert import Alert, Severity


# ANSI color helpers
def _bold(s: str) -> str:
    return f"\033[1m{s}\033[0m"

def _red(s: str) -> str:
    return f"\033[31m{s}\033[0m"

def _green(s: str) -> str:
    return f"\033[32m{s}\033[0m"

def _yellow(s: str) -> str:
    return f"\033[33m{s}\033[0m"

def _cyan(s: str) -> str:
    return f"\033[36m{s}\033[0m"

def _dim(s: str) -> str:
    return f"\033[2m{s}\033[0m"


_STATUS_COLORS: dict[AgentStatus, Any] = {
    AgentStatus.ONLINE: _green,
    AgentStatus.IDLE: _cyan,
    AgentStatus.BUSY: _yellow,
    AgentStatus.ERROR: _red,
    AgentStatus.OFFLINE: _dim,
    AgentStatus.STARTING: _yellow,
    AgentStatus.STOPPING: _yellow,
}

_TASK_COLORS: dict[TaskStatus, Any] = {
    TaskStatus.COMPLETED: _green,
    TaskStatus.RUNNING: _cyan,
    TaskStatus.PENDING: _yellow,
    TaskStatus.FAILED: _red,
    TaskStatus.CANCELLED: _dim,
}

_SEVERITY_COLORS: dict[Severity, Any] = {
    Severity.INFO: _cyan,
    Severity.WARN: _yellow,
    Severity.ERROR: _red,
    Severity.CRITICAL: _red,
}


class DisplayFormatter:
    """Renders fleet state as formatted ASCII tables and sparkline charts.

    Example::

        df = DisplayFormatter()
        print(df.render_agents(agents))
        print(df.render_dashboard(dashboard))
    """

    def __init__(self, use_color: bool = True) -> None:
        self.use_color = use_color

    # ── Agents ────────────────────────────────────────────────────

    def render_agents(self, agents: list[Agent]) -> str:
        if not agents:
            return "No agents registered."

        headers = ["Name", "Status", "Role", "Model", "Host"]
        rows = []
        for a in agents:
            status_str = self._color_status(a.status)
            rows.append([a.name, status_str, a.role, a.model, a.host])

        return self._table(headers, rows)

    # ── Tasks ─────────────────────────────────────────────────────

    def render_tasks(self, tasks: list[Task]) -> str:
        if not tasks:
            return "No tasks."

        headers = ["ID", "Name", "Status", "Priority", "Agent", "Progress"]
        rows = []
        for t in tasks:
            status_str = self._color_task_status(t.status)
            bar = self._progress_bar(t.progress)
            rows.append([t.id[:8], t.name, status_str, str(t.priority), t.agent_id[:8] if t.agent_id else "—", bar])

        return self._table(headers, rows)

    # ── Alerts ────────────────────────────────────────────────────

    def render_alerts(self, alerts: list[Alert], limit: int = 20) -> str:
        if not alerts:
            return "No alerts."

        recent = alerts[-limit:]
        headers = ["#", "Severity", "Message", "Time"]
        rows = []
        for a in reversed(recent):
            sev = self._color_severity(a.severity)
            ts = a.timestamp.strftime("%H:%M:%S")
            msg = a.message[:50] + ("…" if len(a.message) > 50 else "")
            ack = " ✓" if a.acknowledged else ""
            rows.append([str(a.id), sev, msg + ack, ts])

        return self._table(headers, rows)

    # ── Dashboard overview ────────────────────────────────────────

    def render_dashboard(self, dashboard: Any) -> str:
        summary = dashboard.summary()
        lines: list[str] = []

        # Header
        lines.append("╔══════════════════════════════════════════╗")
        lines.append("║      CCC — Central Command Console       ║")
        lines.append("╚══════════════════════════════════════════╝")

        # Agent panel
        a = summary["agents"]
        lines.append("")
        lines.append("┌─ Agents ─────────────────────────────────┐")
        total = a["total"]
        online = self._c(_green(str(a["online"])), self.use_color)
        busy = self._c(_yellow(str(a["busy"])), self.use_color)
        error = self._c(_red(str(a["error"])), self.use_color)
        offline = self._c(_dim(str(a["offline"])), self.use_color)
        lines.append(f"│  Total: {total}  Online: {online}  Busy: {busy}  Error: {error}  Off: {offline}")
        lines.append("└──────────────────────────────────────────┘")

        # Task panel
        t = summary["tasks"]
        lines.append("")
        lines.append("┌─ Tasks ──────────────────────────────────┐")
        lines.append(f"│  Total: {t['total']}  Pending: {t['pending']}  Running: {t['running']}  Done: {t['completed']}  Failed: {t['failed']}")
        lines.append("└──────────────────────────────────────────┘")

        # Metrics panel
        lines.append("")
        lines.append(f"  Metrics recorded: {summary['metrics']}")

        return "\n".join(lines)

    # ── Metrics sparkline ─────────────────────────────────────────

    def render_metric_sparkline(self, metrics: list[HealthMetric], width: int = 30) -> str:
        """Render a sparkline chart of metric values over time."""
        if not metrics:
            return "No data."

        values = [m.value for m in metrics]
        name = metrics[-1].name if metrics else ""
        unit = metrics[-1].unit if metrics else ""

        mn, mx = min(values), max(values)
        rng = mx - mn if mx != mn else 1.0

        # Unicode block characters for sparkline
        chars = "▁▂▃▄▅▆▇█"
        spark = ""
        for v in values[-width:]:
            idx = int((v - mn) / rng * (len(chars) - 1))
            spark += chars[idx]

        return f"  {name}: {spark}  {mn:.1f}–{mx:.1f}{unit}"

    # ── Helpers ───────────────────────────────────────────────────

    def _table(self, headers: list[str], rows: list[list[str]]) -> str:
        """Render a simple ASCII table."""
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                # Strip ANSI for width calculation
                clean = self._strip_ansi(cell)
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(clean))

        # Header
        parts = []
        for i, h in enumerate(headers):
            parts.append(h.ljust(col_widths[i]))
        header_line = "  ".join(parts)

        # Separator
        sep = "─" * len(self._strip_ansi(header_line))

        # Rows
        row_lines = []
        for row in rows:
            parts = []
            for i, cell in enumerate(row):
                clean_len = len(self._strip_ansi(cell))
                pad = col_widths[i] - clean_len
                parts.append(cell + " " * pad)
            row_lines.append("  ".join(parts))

        return f"{header_line}\n{sep}\n" + "\n".join(row_lines)

    @staticmethod
    def _strip_ansi(s: str) -> str:
        """Remove ANSI escape sequences for length calculation."""
        import re
        return re.sub(r"\033\[[0-9;]*m", "", s)

    def _color_status(self, status: AgentStatus) -> str:
        color = _STATUS_COLORS.get(status, str)
        return self._c(color(status.value), self.use_color)

    def _color_task_status(self, status: TaskStatus) -> str:
        color = _TASK_COLORS.get(status, str)
        return self._c(color(status.value), self.use_color)

    def _color_severity(self, severity: Severity) -> str:
        color = _SEVERITY_COLORS.get(severity, str)
        return self._c(color(severity.value), self.use_color)

    @staticmethod
    def _c(colored: str, use_color: bool) -> str:
        return colored if use_color else DisplayFormatter._strip_ansi(colored)

    @staticmethod
    def _progress_bar(progress: float, width: int = 10) -> str:
        filled = int(progress / 100 * width)
        filled = max(0, min(width, filled))
        return "█" * filled + "░" * (width - filled) + f" {progress:.0f}%"
