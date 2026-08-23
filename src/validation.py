import math

def check_rows(csv_list):
    valid_records = []
    errors = []

    for row in csv_list:
        validation_obj = {
            "ticket_id": row["ticket_id"],
            "customer": row["customer"],
            "priority": row["priority"],
            "status": row["status"],
            "hours": None
        }

        row_errors = []

        ticket_id_validation = validate_ticket_id(row["ticket_id"])
        if ticket_id_validation["valid"]:
            validation_obj["ticket_id"] = ticket_id_validation["value"]
        else:
            row_errors.append({
                "field": "ticket_id",
                "invalid_value": row["ticket_id"],
                "reason": ticket_id_validation["error"]
            })

        customer_validation = validate_customer(row["customer"])
        if not customer_validation["valid"]:
            row_errors.append({
                "field": "customer",
                "invalid_value": row["customer"],
                "reason": customer_validation["error"]
            })

        priority_validation = validate_priority(row["priority"])
        if not priority_validation["valid"]:
            row_errors.append({
                "field": "priority",
                "invalid_value": row["priority"],
                "reason": priority_validation["error"]
            })

        status_validation = validate_status(row["status"])
        if not status_validation["valid"]:
            row_errors.append({
                "field": "status",
                "invalid_value": row["status"],
                "reason": status_validation["error"]
            })

        hours_validation = validate_hours(row["hours"])
        if hours_validation["valid"]:
            validation_obj["hours"] = hours_validation["value"]
        else:
            row_errors.append({
                "field": "hours",
                "invalid_value": row["hours"],
                "reason": hours_validation["error"]
            })

        if row_errors:
            validation_obj["errors"] = row_errors
            errors.append(validation_obj)
        else:
            valid_records.append(validation_obj)

    valid_tickets_count = len(valid_records)
    invalid_tickets_count = len(errors)
    total_tickets_count = valid_tickets_count + invalid_tickets_count

    return {
        "valid_records": valid_records,
        "errors": errors,
        "valid_tickets_count": valid_tickets_count,
        "invalid_tickets_count": invalid_tickets_count,
        "total_tickets_count": total_tickets_count
    }


def validate_ticket_id(ticket_id):
    result = {
        "value": None,
        "valid": False,
        "error": None
    }

    if ticket_id is None:
        result["error"] = "ticket_id cannot be [None]"
        return result

    if not isinstance(ticket_id, str):
        result["error"] = f"{ticket_id} must be a string"
        return result

    ticket_id = ticket_id.strip()

    if len(ticket_id) != 4:
        result["error"] = f"{ticket_id} must be exactly 4 characters long"
        return result

    if not ticket_id.isdigit():
        result["error"] = f"{ticket_id} must contain only digits"
        return result

    result["valid"] = True
    result["value"] = ticket_id

    return result


def validate_customer(customer):
    result = {
        "value": None,
        "valid": False,
        "error": None
    }

    if customer is None:
        result["error"] = "customer cannot be [None]"
        return result

    if not isinstance(customer, str):
        result["error"] = f"{customer} must be a string"
        return result

    if not customer.strip():
        result["error"] = "customer cannot be empty"
        return result

    result["valid"] = True
    result["value"] = customer.strip()

    return result


def validate_priority(priority):
    allowed_priorities = {"low", "medium", "high"}

    result = {
        "value": None,
        "valid": False,
        "error": None
    }

    if priority is None:
        result["error"] = "priority cannot be [None]"
        return result

    if not isinstance(priority, str):
        result["error"] = f"{priority} must be a string"
        return result

    priority = priority.strip()

    if priority not in allowed_priorities:
        result["error"] = (
            f"{priority} is invalid; "
            f"must be one of: low, medium, high"
        )
        return result

    result["valid"] = True
    result["value"] = priority

    return result


def validate_status(status):
    allowed_statuses = {"open", "closed", "in_progress"}

    result = {
        "value": None,
        "valid": False,
        "error": None
    }

    if status is None:
        result["error"] = "status cannot be [None]"
        return result

    if not isinstance(status, str):
        result["error"] = f"{status} must be a string"
        return result

    status = status.strip()

    if status not in allowed_statuses:
        result["error"] = (
            f"{status} is invalid; "
            f"must be one of: open, closed, in_progress"
        )
        return result

    result["valid"] = True
    result["value"] = status

    return result


def validate_hours(hours):
    result = {
        "value": None,
        "valid": False,
        "error": None
    }

    if hours is None:
        result["error"] = "hours cannot be [None]"
        return result

    if not isinstance(hours, str):
        result["error"] = f"{hours} must be a string"
        return result

    try:
        clean_hours = float(hours.strip())
    except ValueError:
        result["error"] = f"{hours} is not a number"
        return result

    if not math.isfinite(clean_hours):
        result["error"] = f"{hours} is not a finite number"
        return result

    if clean_hours < 0:
        result["error"] = "hours cannot be less than 0"
        return result

    if clean_hours > 40:
        result["error"] = "hours cannot be greater than 40"
        return result

    if not math.isclose(clean_hours * 2, round(clean_hours * 2)):
        result["error"] = f"{hours} must be in increments of 0.5"
        return result

    result["valid"] = True
    result["value"] = clean_hours

    return result