import math
from collections.abc import Callable
from typing import Any, cast

from ..records import (
    FieldError,
    FieldValidation,
    RawRow,
    TicketRecord,
    ValidationResult
)
from .rules import (
    TICKET_ID_LENGTH,
    MAX_CUSTOMER_LENGTH,
    PRIORITIES,
    STATUSES,
    MIN_HOURS,
    MAX_HOURS,
    HOURS_STEP
)


def validate_row(row: RawRow) -> ValidationResult:
    validation_obj: dict[str, Any] = {
        "ticket_id": row["ticket_id"],
        "customer": row["customer"],
        "priority": row["priority"],
        "status": row["status"],
        "hours": None
    }

    if "_csv_error" in row:
        # The line could not be split into fields properly, so checking
        # the fields would only add misleading errors on top of this one.
        validation_obj["errors"] = [{
            "field": "CSV",
            "invalid_value": row.get("_csv_line", row["_csv_error"]),
            "reason": row["_csv_error"]
        }]

        return {
            "valid": False,
            "record": cast(TicketRecord, validation_obj),
            "error_count": 1
        }

    row_errors: list[FieldError] = []

    ticket_id_validation = validate_ticket_id(
        row["ticket_id"]
    )

    if ticket_id_validation["valid"]:
        validation_obj["ticket_id"] = (
            ticket_id_validation["value"]
        )
    else:
        row_errors.append({
            "field": "ticket_id",
            "invalid_value": row["ticket_id"],
            "reason": (
                ticket_id_validation["error"] or "invalid value"
            )
        })

    customer_validation = validate_customer(
        row["customer"]
    )

    if customer_validation["valid"]:
        validation_obj["customer"] = (
            customer_validation["value"]
        )
    else:
        row_errors.append({
            "field": "customer",
            "invalid_value": row["customer"],
            "reason": (
                customer_validation["error"] or "invalid value"
            )
        })

    priority_validation = validate_priority(
        row["priority"]
    )

    if priority_validation["valid"]:
        validation_obj["priority"] = (
            priority_validation["value"]
        )
    else:
        row_errors.append({
            "field": "priority",
            "invalid_value": row["priority"],
            "reason": (
                priority_validation["error"] or "invalid value"
            )
        })

    status_validation = validate_status(
        row["status"]
    )

    if status_validation["valid"]:
        validation_obj["status"] = (
            status_validation["value"]
        )
    else:
        row_errors.append({
            "field": "status",
            "invalid_value": row["status"],
            "reason": (
                status_validation["error"] or "invalid value"
            )
        })

    hours_validation = validate_hours(
        row["hours"]
    )

    if hours_validation["valid"]:
        validation_obj["hours"] = (
            hours_validation["value"]
        )
    else:
        row_errors.append({
            "field": "hours",
            "invalid_value": row["hours"],
            "reason": (
                hours_validation["error"] or "invalid value"
            )
        })

    if row_errors:
        validation_obj["errors"] = row_errors

        return {
            "valid": False,
            "record": cast(TicketRecord, validation_obj),
            "error_count": len(row_errors)
        }

    return {
        "valid": True,
        "record": cast(TicketRecord, validation_obj),
        "error_count": 0
    }


def flag_duplicate_ticket(
    row: RawRow,
    validation_result: ValidationResult,
    duplicate_counts: dict[str, int]
) -> ValidationResult:
    """Make a row invalid if its ticket_id appears more than once.

    duplicate_counts is what find_duplicate_ticket_ids() returned:
    {ticket_id: times_it_appears}. Every row that shares a ticket_id is
    flagged, so both rows of a pair are invalid, not just the second one.
    The row keeps any other errors it already had.
    """
    if not duplicate_counts or "_csv_error" in row:
        return validation_result

    record = validation_result["record"]

    # A valid ticket_id has already been cleaned (whitespace stripped)
    # in the record. An invalid one is never in duplicate_counts.
    times = duplicate_counts.get(record["ticket_id"])

    if times is None:
        return validation_result

    flagged = record.copy()
    flagged["errors"] = record.get("errors", []) + [{
        "field": "ticket_id",
        "invalid_value": record["ticket_id"],
        "reason": (
            f"duplicate ticket_id: appears {times} times in the file"
        )
    }]

    return {
        "valid": False,
        "record": flagged,
        "error_count": validation_result["error_count"] + 1
    }


def validate_ticket_id(ticket_id: Any) -> FieldValidation:
    result: FieldValidation = {
        "value": None,
        "valid": False,
        "error": None
    }

    if ticket_id is None:
        result["error"] = "ticket_id cannot be [None]"
        return result

    if not isinstance(ticket_id, str):
        result["error"] = (
            f"{ticket_id} must be a string"
        )
        return result

    ticket_id = ticket_id.strip()

    if len(ticket_id) != TICKET_ID_LENGTH:
        result["error"] = (
            f"{ticket_id} must be exactly "
            f"{TICKET_ID_LENGTH} characters long"
        )
        return result

    # isdigit() alone also accepts digits from other scripts ("²", "٣").
    if not (ticket_id.isascii() and ticket_id.isdigit()):
        result["error"] = (
            f"{ticket_id} must contain only digits"
        )
        return result

    result["valid"] = True
    result["value"] = ticket_id

    return result


def validate_customer(customer: Any) -> FieldValidation:
    result: FieldValidation = {
        "value": None,
        "valid": False,
        "error": None
    }

    if customer is None:
        result["error"] = (
            "customer cannot be [None]"
        )
        return result

    if not isinstance(customer, str):
        result["error"] = (
            f"{customer} must be a string"
        )
        return result

    if not customer.strip():
        result["error"] = (
            "customer cannot be empty"
        )
        return result

    if len(customer) > MAX_CUSTOMER_LENGTH:
        result["error"] = (
            f"customer cannot have a length greater than "
            f"{MAX_CUSTOMER_LENGTH}"
        )
        return result

    result["valid"] = True
    result["value"] = customer.strip()

    return result


def validate_priority(priority: Any) -> FieldValidation:
    result: FieldValidation = {
        "value": None,
        "valid": False,
        "error": None
    }

    if priority is None:
        result["error"] = (
            "priority cannot be [None]"
        )
        return result

    if not isinstance(priority, str):
        result["error"] = (
            f"{priority} must be a string"
        )
        return result

    priority = priority.strip()

    if priority not in PRIORITIES:
        result["error"] = (
            f"{priority} is not a valid priority"
        )
        return result

    result["valid"] = True
    result["value"] = priority

    return result


def validate_status(status: Any) -> FieldValidation:
    result: FieldValidation = {
        "value": None,
        "valid": False,
        "error": None
    }

    if status is None:
        result["error"] = (
            "status cannot be [None]"
        )
        return result

    if not isinstance(status, str):
        result["error"] = (
            f"{status} must be a string"
        )
        return result

    status = status.strip()

    if status not in STATUSES:
        result["error"] = (
            f"{status} is not a valid status"
        )
        return result

    result["valid"] = True
    result["value"] = status

    return result


def validate_hours(hours: Any) -> FieldValidation:
    result: FieldValidation = {
        "value": None,
        "valid": False,
        "error": None
    }

    if hours is None:
        result["error"] = (
            "hours cannot be [None]"
        )
        return result

    if not isinstance(hours, str):
        result["error"] = (
            f"{hours} must be a string"
        )
        return result

    try:
        clean_hours = float(hours.strip())
    except ValueError:
        result["error"] = (
            f"{hours} must be a number"
        )
        return result

    if not math.isfinite(clean_hours):
        result["error"] = (
            f"{hours} must be a finite number"
        )
        return result

    if clean_hours < MIN_HOURS:
        result["error"] = (
            f"{hours} cannot be less than {MIN_HOURS}"
        )
        return result

    if clean_hours > MAX_HOURS:
        result["error"] = (
            f"{hours} cannot be greater than {MAX_HOURS}"
        )
        return result

    steps = clean_hours / HOURS_STEP

    if not math.isclose(steps, round(steps)):
        result["error"] = (
            f"{hours} must be in increments of {HOURS_STEP}"
        )
        return result

    result["valid"] = True
    result["value"] = clean_hours

    return result