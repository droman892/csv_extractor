from pathlib import Path
import csv
import shutil
import tempfile


class ResultsExportService:

    @staticmethod
    def create_export_file(result):
        temp_directory = Path(
            tempfile.mkdtemp(
                prefix="csv_extractor_"
            )
        )

        export_path = (
            temp_directory
            / f"{Path(result['filename']).stem}_results.csv"
        )

        ResultsExportService.export_results(
            result,
            export_path
        )

        return str(export_path)

    @staticmethod
    def export_results(result, destination_path):
        try:
            with open(
                destination_path,
                "w",
                newline="",
                encoding="utf-8"
            ) as csv_file:

                writer = csv.writer(csv_file)

                ResultsExportService._write_title_section(
                    writer,
                    result
                )

                ResultsExportService._write_overall_section(
                    writer,
                    result
                )

                ResultsExportService._write_status_section(
                    writer,
                    result
                )

                ResultsExportService._write_priority_section(
                    writer,
                    result
                )

                ResultsExportService._write_customer_section(
                    writer,
                    result
                )

                ResultsExportService._write_validation_section(
                    writer,
                    result
                )

        except KeyError as error:
            raise ValueError(
                f"Unable to export results because required "
                f"result data is missing: {error}"
            ) from error

        except OSError as error:
            raise OSError(
                f"Unable to write the export file "
                f"'{destination_path}': {error}"
            ) from error

        except Exception as error:
            raise RuntimeError(
                f"An unexpected error occurred while exporting "
                f"the results: {error}"
            ) from error

    @staticmethod
    def _write_title_section(writer, result):
        writer.writerow([
            "CSV Extractor Results"
        ])

        writer.writerow([
            "Filename",
            Path(result["filename"]).name
        ])

        writer.writerow([
            "Note: Only data from valid records is included in Tickets by Status, Tickets by Priority, and Hours by Customer."
        ])

        writer.writerow([])

    @staticmethod
    def _write_overall_section(writer, result):
        writer.writerow([
            "Overall"
        ])

        writer.writerow([
            "Metric",
            "Count"
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

    @staticmethod
    def _write_status_section(writer, result):
        writer.writerow([
            "Tickets by Status"
        ])

        writer.writerow([
            "Status",
            "Count"
        ])

        for status, count in (
            result["summary"]["tickets_by_status"].items()
        ):
            writer.writerow([
                status.replace(
                    "_",
                    " "
                ).title(),
                count
            ])

        writer.writerow([])

    @staticmethod
    def _write_priority_section(writer, result):
        writer.writerow([
            "Tickets by Priority"
        ])

        writer.writerow([
            "Priority",
            "Count"
        ])

        for priority, count in (
            result["summary"]["tickets_by_priority"].items()
        ):
            writer.writerow([
                priority.replace(
                    "_",
                    " "
                ).title(),
                count
            ])

        writer.writerow([])

    @staticmethod
    def _write_customer_section(writer, result):
        customers = result["summary"]["hours_by_customer"]

        total_customer_count = len(customers)

        writer.writerow([
            f"Hours by Customer (Count: {total_customer_count})"
        ])

        writer.writerow([
            "Customer #",
            "Customer",
            "Hours"
        ])

        customers = sorted(
            customers.items(),
            key=lambda item: str(item[0]).lower()
        )

        customer_number = 1

        for customer, hours in customers:
            writer.writerow([
                customer_number,
                customer,
                hours
            ])

            customer_number += 1

        writer.writerow([])

    @staticmethod
    def _write_validation_section(writer, result):
        invalid_records = result["invalid_records"]

        total_invalid_error_count = sum(
            len(record.get("errors", []))
            for record in invalid_records
        )

        writer.writerow([
            f"Validation Issues (Count: "
            f"{total_invalid_error_count})"
        ])

        writer.writerow([
            "Issue #",
            "Ticket",
            "Field",
            "Invalid Value",
            "Validation Error"
        ])

        issue_number = 1

        for record in invalid_records:
            for error in record.get("errors", []):
                writer.writerow([
                    issue_number,
                    record["ticket_id"],
                    error["field"],
                    error["invalid_value"],
                    error["reason"]
                ])

                issue_number += 1

    @staticmethod
    def copy_export_file(source_path, destination_path):
        try:
            shutil.copyfile(
                source_path,
                destination_path
            )

        except OSError as error:
            raise OSError(
                f"Unable to save the exported file "
                f"to '{destination_path}': {error}"
            ) from error