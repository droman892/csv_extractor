import os


class ResultsViewModel:

    def __init__(self, result):
        self.display_result = result["display_result"]
        self.export_file = result["export_file"]

    def get_filename(self):
        return os.path.basename(
            self.display_result["filename"]
        )

    def get_summary(self):
        return {
            "total_tickets_count":
                self.display_result["total_tickets_count"],

            "valid_tickets_count":
                self.display_result["valid_tickets_count"],

            "invalid_tickets_count":
                self.display_result["invalid_tickets_count"],

            "total_hours":
                self.display_result["summary"]["total_hours"],

            "tickets_by_status":
                self.display_result["summary"]["tickets_by_status"],

            "tickets_by_priority":
                self.display_result["summary"]["tickets_by_priority"],

            "hours_by_customer":
                self.display_result["summary"]["hours_by_customer"]
        }

    def get_invalid_rows(self):
        return self.display_result["invalid_records"]

    def get_customer_rows(self):
        return list(
            self.display_result[
                "summary"
            ]["hours_by_customer"].items()
        )

    def get_total_customer_count(self):
        return self.display_result[
            "total_customer_count"
        ]

    def get_total_invalid_record_count(self):
        return self.display_result[
            "total_invalid_record_count"
        ]

    def get_export_file(self):
        return self.export_file