def aggregate_csv(valid_records):

    tickets_by_status = {}
    tickets_by_priority = {}
    hours_by_customer = {}
    total_hours = 0

    for row in valid_records:
        if row["status"] not in tickets_by_status:
            tickets_by_status[row["status"]] = 1
        else:
            tickets_by_status[row["status"]] += 1

        if row["priority"] not in tickets_by_priority:
            tickets_by_priority[row["priority"]] = 1
        else:
            tickets_by_priority[row["priority"]] += 1

        if row["customer"] not in hours_by_customer:
            hours_by_customer[row["customer"]] = row["hours"]
        else:
            hours_by_customer[row["customer"]] += row["hours"]

        total_hours += row["hours"]

    result = {
        "tickets_by_status": tickets_by_status,
        "tickets_by_priority": tickets_by_priority,
        "hours_by_customer": hours_by_customer,
        "total_hours": total_hours
    }

    return result