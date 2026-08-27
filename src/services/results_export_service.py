import csv
from pathlib import Path


class ResultsExportService:
    @staticmethod
    def export_results(result, destination_path):
        path = Path(destination_path)

        with path.open(
            mode="w",
            newline="",
            encoding="utf-8"
        ) as file:
            writer = csv.writer(file)

            writer.writerow(["SUMMARY"])
            writer.writerow(["Metric", "Value"])
            writer.writerow([
                "Filename",
                Path(result["filename"]).name
            ])
            writer.writerow([
                "Total Tickets",
                result["total_tickets_count"]
            ])
            writer.writerow([
                "Valid Tickets",
                result["valid_tickets_count"]
            ])
            writer.writerow([
                "Invalid Tickets",
                result["invalid_tickets_count"]
            ])
            writer.writerow([
                "Total Hours",
                result["summary"]["total_hours"]
            ])

            writer.writerow([])
            writer.writerow(["TICKETS BY STATUS"])
            writer.writerow(["Status", "Count"])

            for status, count in result["summary"][
                "tickets_by_status"
            ].items():
                writer.writerow([
                    status.replace("_", " ").title(),
                    count
                ])

            writer.writerow([])
            writer.writerow(["TICKETS BY PRIORITY"])
            writer.writerow(["Priority", "Count"])

            for priority, count in result["summary"][
                "tickets_by_priority"
            ].items():
                writer.writerow([
                    priority.replace("_", " ").title(),
                    count
                ])

            writer.writerow([])
            writer.writerow(["HOURS BY CUSTOMER"])
            writer.writerow(["Customer", "Hours"])

            for customer, hours in result["summary"][
                "hours_by_customer"
            ].items():
                writer.writerow([
                    customer,
                    hours
                ])

            writer.writerow([])
            writer.writerow(["VALIDATION ISSUES"])
            writer.writerow([
                "Issue #",
                "Ticket",
                "Field",
                "Invalid Value",
                "Validation Error"
            ])

            issue_number = 1

            for record in result["invalid_records"]:
                for error in record["errors"]:
                    writer.writerow([
                        issue_number,
                        record["ticket_id"],
                        error["field"],
                        error["invalid_value"],
                        error["reason"]
                    ])

                    issue_number += 1