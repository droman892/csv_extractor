"""The ticket validation rules, defined once.

Validation, aggregation and the format hints on the upload screen all read
these values, so a rule can only be changed in one place and the screen
cannot drift out of step with what validation actually enforces.
"""

from ..config import MAX_LINE_LENGTH

TICKET_ID_LENGTH: int = 9
MAX_CUSTOMER_LENGTH: int = 30

# The order here is the order shown in the results and in the export.
PRIORITIES: tuple[str, ...] = ("low", "medium", "high")
STATUSES: tuple[str, ...] = ("open", "closed", "in_progress")

MIN_HOURS: float = 0.5
MAX_HOURS: float = 40
HOURS_STEP: float = 0.5

FORMAT_NOTE: str = (
    f"One record per line, up to {MAX_LINE_LENGTH:,} characters long."
)

# Shown on the results screen and written to the top of the export. The
# export writes it as a plain line, not as a quoted CSV cell, so it must
# not contain quotes or line breaks.
VALID_RECORDS_NOTE: str = (
    "Note: Only data from valid records is included in these sections: "
    "Tickets by Status, Tickets by Priority, and Hours by Customer."
)


def _join_choices(choices: tuple[str, ...]) -> str:
    """('a', 'b', 'c') -> 'a, b, or c'"""
    if len(choices) < 3:
        return " or ".join(choices)

    return ", ".join(choices[:-1]) + ", or " + choices[-1]


def format_hints() -> list[tuple[str, str]]:
    """(column, description) pairs for the 'Expected CSV Format' table."""
    return [
        ("ticket_id", f"Exactly {TICKET_ID_LENGTH} digits"),
        ("customer", f"Required, up to {MAX_CUSTOMER_LENGTH} characters"),
        ("priority", _join_choices(PRIORITIES)),
        ("status", _join_choices(STATUSES)),
        (
            "hours",
            f"{MIN_HOURS:g}–{MAX_HOURS:g}, "
            f"in increments of {HOURS_STEP:g}"
        ),
    ]
