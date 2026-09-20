"""The shapes of the data passed between the layers.

These are TypedDicts: at run time they are ordinary dicts (so the code and
its tests can build and compare them as plain dicts), and a type checker
such as mypy can check the keys and value types.
"""

from pathlib import Path
from typing import Any, NotRequired, TypedDict

# One line of the CSV file, keyed by the column names in the header.
# A line that could not be parsed also has "_csv_error" and "_csv_line".
RawRow = dict[str, str]

# What a background process puts on its queue: ("completed" | "failed", value)
WorkerMessage = tuple[str, Any]


class FieldError(TypedDict):
    field: str
    invalid_value: str
    reason: str


class TicketRecord(TypedDict):
    """A validated row. Cleaned values where valid, raw text where not."""

    ticket_id: str
    customer: str
    priority: str
    status: str
    hours: float | None
    errors: NotRequired[list[FieldError]]


class InvalidTicket(TypedDict):
    """What the report needs to know about one invalid ticket.

    A TicketRecord has these keys too, so it can be used where an
    InvalidTicket is expected.
    """

    ticket_id: str
    errors: NotRequired[list[FieldError]]


class FieldValidation(TypedDict):
    """The outcome of validating one field."""

    value: Any  # cleaned value (str, or float for hours); None if invalid
    valid: bool
    error: str | None


class ValidationResult(TypedDict):
    valid: bool
    record: TicketRecord
    error_count: int


class Summary(TypedDict):
    tickets_by_status: dict[str, int]
    tickets_by_priority: dict[str, int]
    hours_by_customer: dict[str, float]
    total_hours: float


class ProcessingResult(TypedDict):
    """The full result of processing a file (saved to the result file)."""

    filename: str | Path
    summary: Summary
    valid_tickets_count: int
    invalid_tickets_count: int
    total_tickets_count: int
    total_validation_error_count: int

    # Either every invalid ticket is in this list, or (when the processor
    # was given a file to write them to) the list is empty and
    # invalid_details_path names that file. Use iter_invalid_tickets() in
    # src/processing/invalid_tickets.py to read them either way.
    invalid_records: list[TicketRecord]
    invalid_details_path: NotRequired[str]


class DisplayIssue(TypedDict):
    """One validation error, flattened for the results table."""

    ticket_id: str
    field: str
    invalid_value: str
    reason: str


class DisplaySummary(TypedDict):
    total_hours: float
    tickets_by_status: dict[str, int]
    tickets_by_priority: dict[str, int]
    hours_by_customer: dict[str, float]


class DisplayResult(TypedDict):
    """The small part of a result that is shown on screen."""

    filename: str | Path
    total_tickets_count: int
    valid_tickets_count: int
    invalid_tickets_count: int
    summary: DisplaySummary
    invalid_records: list[DisplayIssue]
    total_customer_count: int
    total_invalid_record_count: int
    total_invalid_error_count: int


class CompletedPayload(TypedDict):
    display_result: DisplayResult
    full_result_path: str
