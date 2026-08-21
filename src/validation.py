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

        hours = row["hours"]
        hours_validation = validate_hours(hours)

        if hours_validation["valid"]:
            validation_obj["hours"] = hours_validation["value"]
            valid_records.append(validation_obj)
        else:
            validation_obj["invalid_value"] = hours
            validation_obj["reason"] = hours_validation["error"]
            errors.append(validation_obj)

    valid_tickets_count = len(valid_records)
    invalid_tickets_count = len(errors)
    total_tickets_count = valid_tickets_count + invalid_tickets_count

    processed_rows = {
        "valid_records": valid_records,
        "errors": errors,
        "valid_tickets_count": valid_tickets_count,
        "invalid_tickets_count": invalid_tickets_count,
        "total_tickets_count": total_tickets_count
    }

    return processed_rows

def validate_hours(hours):
    result = {
        "hours": hours,
        "value": None,
        "valid": False,
        "error": None
    }

    if hours is None:
        result["error"] = "hours cannot be [None]"
        return result
    elif not isinstance(hours, str):
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
    elif clean_hours < 0:
        result["error"] = "hours cannot be less than 0"
        return result
    elif clean_hours > 24:
        result["error"] = "hours cannot be greater than 24"
        return result

    result["valid"] = True
    result["value"] = clean_hours
    return result