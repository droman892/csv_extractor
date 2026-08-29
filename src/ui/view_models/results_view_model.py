import os


class ResultsViewModel:

    def __init__(self, result):
        self.result = result

    def get_filename(self):
        return os.path.basename(
            self.result["filename"]
        )

    def get_summary(self):
        return {
            "total_tickets_count":
                self.result["total_tickets_count"],

            "valid_tickets_count":
                self.result["valid_tickets_count"],

            "invalid_tickets_count":
                self.result["invalid_tickets_count"],

            "total_hours":
                self.result["summary"]["total_hours"],

            "tickets_by_status":
                self.result["summary"]["tickets_by_status"],

            "tickets_by_priority":
                self.result["summary"]["tickets_by_priority"],

            "hours_by_customer":
                self.result["summary"]["hours_by_customer"]
        }

    def get_invalid_rows(self):
        return self.result["invalid_records"]

    def get_customer_rows(self):
        return list(
            self.result["summary"][
                "hours_by_customer"
            ].items()
        )

    def get_total_customer_count(self):
        return self.result[
            "total_customer_count"
        ]

    def get_total_invalid_record_count(self):
        return self.result[
            "total_invalid_record_count"
        ]

    def get_total_invalid_error_count(self):
        return self.result[
            "total_invalid_error_count"
        ]