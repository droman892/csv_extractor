import csv
import re
from pathlib import Path
from typing import Any

from ..processing.invalid_tickets import iter_invalid_tickets
from ..processing.rules import VALID_RECORDS_NOTE
from ..records import ProcessingResult


# A cell that starts with one of these is treated as a formula by Excel,
# Google Sheets and LibreOffice, so text from the input file could run
# code or leak data when someone opens the export ("CSV injection").
FORMULA_TRIGGERS = ("=", "+", "-", "@", "\t", "\r")

PLAIN_NUMBER = re.compile(r"[+-]?\d+(\.\d+)?")


def safe_cell(value: Any) -> Any:
    """Make text from the input file safe to write into an export cell.

    A leading apostrophe makes spreadsheets treat the cell as plain text.
    Non-strings (counts, hours) and plain numbers such as "-3.0" are left
    alone: a bare number cannot run a formula, and the Invalid Value
    column often holds exactly such a number.
    """
    if (
        isinstance(value, str)
        and value.startswith(FORMULA_TRIGGERS)
        and not PLAIN_NUMBER.fullmatch(value)
    ):
        return "'" + value

    return value


class ResultsExportService:

    @staticmethod
    def export_results(
        result: ProcessingResult,
        destination_path: str | Path
    ) -> None:
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
                    csv_file,
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
    def _write_title_section(
        writer: Any,
        csv_file: Any,
        result: ProcessingResult
    ) -> None:
        writer.writerow([
            "CSV Extractor Results"
        ])

        writer.writerow([
            "Filename",
            safe_cell(Path(result["filename"]).name)
        ])

        # Written as a plain line so a text editor shows it without
        # quotes. The csv writer would wrap it in quotes because of its
        # commas. The cost: a spreadsheet splits the line at the commas
        # into several cells. The note is fixed text with no quotes or
        # line breaks (checked by a test), so nothing else can go wrong.
        csv_file.write(VALID_RECORDS_NOTE + "\r\n")

        writer.writerow([])

    @staticmethod
    def _write_overall_section(
        writer: Any,
        result: ProcessingResult
    ) -> None:
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
    def _write_status_section(
        writer: Any,
        result: ProcessingResult
    ) -> None:
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
    def _write_priority_section(
        writer: Any,
        result: ProcessingResult
    ) -> None:
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
    def _write_customer_section(
        writer: Any,
        result: ProcessingResult
    ) -> None:
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

        sorted_customers = sorted(
            customers.items(),
            key=lambda item: str(item[0]).lower()
        )

        customer_number = 1

        for customer, hours in sorted_customers:
            writer.writerow([
                customer_number,
                safe_cell(customer),
                hours
            ])

            customer_number += 1

        writer.writerow([])

    @staticmethod
    def _write_validation_section(
        writer: Any,
        result: ProcessingResult
    ) -> None:
        total_invalid_error_count = result.get(
            "total_validation_error_count"
        )

        if total_invalid_error_count is None:
            total_invalid_error_count = sum(
                len(record.get("errors", []))
                for record in iter_invalid_tickets(result)
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

        # Read one ticket at a time: there can be millions.
        for record in iter_invalid_tickets(result):
            for error in record.get("errors", []):
                writer.writerow([
                    issue_number,
                    safe_cell(record["ticket_id"]),
                    safe_cell(error["field"]),
                    safe_cell(error["invalid_value"]),
                    safe_cell(error["reason"])
                ])

                issue_number += 1
