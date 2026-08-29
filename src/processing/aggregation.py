def aggregate_csv(valid_records):
    tickets_by_status = {
        "open": 0,
        "closed": 0,
        "in_progress": 0
    }

    tickets_by_priority = {
        "low": 0,
        "medium": 0,
        "high": 0
    }

    hours_by_customer = {}
    total_hours = 0

    for row in valid_records:
        tickets_by_status[row["status"]] += 1
        tickets_by_priority[row["priority"]] += 1

        if row["customer"] not in hours_by_customer:
            hours_by_customer[row["customer"]] = row["hours"]
        else:
            hours_by_customer[row["customer"]] += row["hours"]

        total_hours += row["hours"]

    return {
        "tickets_by_status": tickets_by_status,
        "tickets_by_priority": tickets_by_priority,
        "hours_by_customer": hours_by_customer,
        "total_hours": total_hours
    }