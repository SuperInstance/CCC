"""CCC — Central Command Console.

A unified dashboard for monitoring and controlling agent fleets.
"""

from ccc.console import Console
from ccc.dashboard import Dashboard
from ccc.command import CommandParser
from ccc.alert import AlertManager, Severity
from ccc.display import DisplayFormatter

__version__ = "0.1.0"
__all__ = [
    "Console",
    "Dashboard",
    "CommandParser",
    "AlertManager",
    "Severity",
    "DisplayFormatter",
]
