"""Tests for AlertManager."""

from ccc.alert import AlertManager, Alert, Severity, EscalationRule


class TestAlertManager:
    def test_emit_levels(self):
        am = AlertManager()
        am.info("info msg")
        am.warn("warn msg")
        am.error("error msg")
        am.critical("crit msg")
        assert len(am.alerts) == 4

    def test_unacknowledged(self):
        am = AlertManager()
        am.info("a")
        am.warn("b")
        am.acknowledge(1)
        assert len(am.unacknowledged()) == 1

    def test_by_severity(self):
        am = AlertManager()
        am.warn("w1")
        am.warn("w2")
        am.error("e1")
        assert len(am.by_severity(Severity.WARN)) == 2
        assert len(am.by_severity(Severity.ERROR)) == 1

    def test_acknowledge_all(self):
        am = AlertManager()
        am.info("a")
        am.info("b")
        am.info("c")
        count = am.acknowledge_all()
        assert count == 3
        assert len(am.unacknowledged()) == 0

    def test_notification_channel(self):
        received = []
        am = AlertManager()
        am.add_channel("test", lambda a: received.append(a.message))
        am.warn("hello")
        assert received == ["hello"]

    def test_channel_exception_handled(self):
        am = AlertManager()
        am.add_channel("bad", lambda a: 1 / 0)
        am.add_channel("good", lambda a: None)
        # Should not raise
        am.info("safe")

    def test_escalation_rule(self):
        am = AlertManager()
        am.add_escalation_rule(EscalationRule(
            min_severity=Severity.WARN,
            after_count=2,
            target_severity=Severity.CRITICAL,
        ))
        am.warn("first")
        am.warn("second")
        # Both should be escalated to critical
        escalated = [a for a in am.alerts if a.escalated]
        assert len(escalated) == 2
        assert all(a.severity == Severity.CRITICAL for a in escalated)

    def test_clear(self):
        am = AlertManager()
        am.info("a")
        am.info("b")
        am.clear()
        assert len(am.alerts) == 0

    def test_clear_acknowledged(self):
        am = AlertManager()
        am.info("a")
        am.warn("b")
        am.acknowledge(1)
        removed = am.clear_acknowledged()
        assert removed == 1
        assert len(am.alerts) == 1

    def test_max_alerts_trimming(self):
        am = AlertManager(max_alerts=5)
        for i in range(10):
            am.info(f"msg-{i}")
        assert len(am.alerts) == 5
        assert am.alerts[0].message == "msg-5"

    def test_severity_ordering(self):
        assert Severity.CRITICAL > Severity.ERROR
        assert Severity.ERROR > Severity.WARN
        assert Severity.WARN > Severity.INFO
        assert Severity.INFO >= Severity.INFO
