"""AlertManager — severity levels, escalation rules, notification channels."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable


class Severity(str, enum.Enum):
    """Alert severity levels."""

    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    CRITICAL = "critical"

    @property
    def weight(self) -> int:
        return {Severity.INFO: 0, Severity.WARN: 1, Severity.ERROR: 2, Severity.CRITICAL: 3}[self]

    def __ge__(self, other: "Severity") -> bool:
        return self.weight >= other.weight

    def __gt__(self, other: "Severity") -> bool:
        return self.weight > other.weight

    def __le__(self, other: "Severity") -> bool:
        return self.weight <= other.weight

    def __lt__(self, other: "Severity") -> bool:
        return self.weight < other.weight


# Notification channel callback: receives (alert) -> None
NotificationChannel = Callable[["Alert"], None]


@dataclass
class Alert:
    """A single alert event."""

    message: str
    severity: Severity = Severity.INFO
    source: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    escalated: bool = False
    id: int = 0


@dataclass
class EscalationRule:
    """Rule that auto-escalates alerts after a threshold.

    Attributes:
        min_severity: Minimum severity to consider.
        after_count: Escalate after this many unacknowledged alerts at or above min_severity.
        target_severity: Escalate to this severity level.
    """

    min_severity: Severity = Severity.WARN
    after_count: int = 3
    target_severity: Severity = Severity.CRITICAL


class AlertManager:
    """Manages alerts with severity levels, escalation, and notification channels.

    Example::

        am = AlertManager()
        am.add_channel("log", lambda a: print(f"[{a.severity.value}] {a.message}"))
        am.warn("Agent forge1 is unreachable")
        am.critical("Disk full on host node-3")

        unacked = am.unacknowledged()
    """

    def __init__(self, max_alerts: int = 500) -> None:
        self._alerts: list[Alert] = []
        self._max_alerts = max_alerts
        self._next_id = 1
        self._channels: dict[str, NotificationChannel] = {}
        self._escalation_rules: list[EscalationRule] = []

    # ── Notification channels ─────────────────────────────────────

    def add_channel(self, name: str, handler: NotificationChannel) -> None:
        """Register a notification channel."""
        self._channels[name] = handler

    def remove_channel(self, name: str) -> bool:
        return self._channels.pop(name, None) is not None

    # ── Escalation rules ──────────────────────────────────────────

    def add_escalation_rule(self, rule: EscalationRule) -> None:
        self._escalation_rules.append(rule)

    # ── Emit alerts ───────────────────────────────────────────────

    def _emit(self, message: str, severity: Severity, source: str = "") -> Alert:
        alert = Alert(
            message=message,
            severity=severity,
            source=source,
            id=self._next_id,
        )
        self._next_id += 1
        self._alerts.append(alert)
        if len(self._alerts) > self._max_alerts:
            self._alerts = self._alerts[-self._max_alerts:]

        # Notify channels
        for handler in self._channels.values():
            try:
                handler(alert)
            except Exception:
                pass

        # Check escalation
        self._check_escalation()
        return alert

    def info(self, message: str, source: str = "") -> Alert:
        return self._emit(message, Severity.INFO, source)

    def warn(self, message: str, source: str = "") -> Alert:
        return self._emit(message, Severity.WARN, source)

    def error(self, message: str, source: str = "") -> Alert:
        return self._emit(message, Severity.ERROR, source)

    def critical(self, message: str, source: str = "") -> Alert:
        return self._emit(message, Severity.CRITICAL, source)

    # ── Query ─────────────────────────────────────────────────────

    @property
    def alerts(self) -> list[Alert]:
        return list(self._alerts)

    def unacknowledged(self) -> list[Alert]:
        return [a for a in self._alerts if not a.acknowledged]

    def by_severity(self, severity: Severity) -> list[Alert]:
        return [a for a in self._alerts if a.severity == severity]

    def get(self, alert_id: int) -> Alert | None:
        for a in self._alerts:
            if a.id == alert_id:
                return a
        return None

    # ── Acknowledge ───────────────────────────────────────────────

    def acknowledge(self, alert_id: int) -> bool:
        alert = self.get(alert_id)
        if alert is None:
            return False
        alert.acknowledged = True
        return True

    def acknowledge_all(self) -> int:
        count = 0
        for a in self._alerts:
            if not a.acknowledged:
                a.acknowledged = True
                count += 1
        return count

    # ── Escalation ────────────────────────────────────────────────

    def _check_escalation(self) -> None:
        for rule in self._escalation_rules:
            unacked = [
                a for a in self._alerts
                if not a.acknowledged and a.severity >= rule.min_severity
            ]
            if len(unacked) >= rule.after_count:
                for a in unacked:
                    if not a.escalated:
                        a.escalated = True
                        a.severity = max(a.severity, rule.target_severity, key=lambda s: s.weight)

    # ── Clear ─────────────────────────────────────────────────────

    def clear(self) -> None:
        self._alerts.clear()

    def clear_acknowledged(self) -> int:
        before = len(self._alerts)
        self._alerts = [a for a in self._alerts if not a.acknowledged]
        return before - len(self._alerts)
