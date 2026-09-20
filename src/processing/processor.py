import contextlib
import logging
import os
import time
from pathlib import Path

from ..records import ProcessingResult, TicketRecord
from .csv_reader import read_csv
from .duplicates import find_duplicate_ticket_ids
from .invalid_tickets import open_for_writing, write_invalid_ticket
from .validation import validate_row, flag_duplicate_ticket
from .aggregation import (
    create_aggregation,
    add_valid_record
)


logger = logging.getLogger(__name__)


def process_csv(
    filename: str | Path,
    invalid_details_path: str | Path | None = None
) -> ProcessingResult:
    """Validate and aggregate a CSV file.

    The file is read twice. The first pass finds ticket_ids that appear
    more than once, because a row cannot be judged a duplicate until the
    whole file has been seen. The second pass validates each row and
    marks every row that shares a ticket_id as invalid.

    Memory: rows are never held all at once. What does stay in memory is
    the set of distinct valid ticket_ids (pass 1) and one total per
    customer. The invalid tickets are the part that can be huge, so:

    - With invalid_details_path, each invalid ticket is written to that
      file (which must not exist yet) as it is found. "invalid_records"
      in the result is then empty and "invalid_details_path" names the
      file. The caller owns the file; it is deleted here only if
      processing fails.
    - Without it, every invalid ticket is kept in "invalid_records".
      Fine for small files and tests; the application always passes a
      path.

    Either way, read them with iter_invalid_tickets().
    """
    started = time.monotonic()
    logger.info("Processing %s", Path(filename).name)

    duplicate_counts = find_duplicate_ticket_ids(filename)

    logger.info(
        "Pass 1 found %d ticket_ids that appear more than once",
        len(duplicate_counts)
    )

    summary = create_aggregation()

    invalid_records: list[TicketRecord] = []

    valid_tickets_count = 0
    invalid_tickets_count = 0
    total_tickets_count = 0
    total_validation_error_count = 0

    details_file = (
        open_for_writing(invalid_details_path)
        if invalid_details_path is not None
        else None
    )

    try:

        for raw_row in read_csv(filename):

            validation_result = validate_row(
                raw_row
            )

            validation_result = flag_duplicate_ticket(
                raw_row,
                validation_result,
                duplicate_counts
            )

            total_tickets_count += 1

            if validation_result["valid"]:

                add_valid_record(
                    summary,
                    validation_result["record"]
                )

                valid_tickets_count += 1

            else:

                if details_file is not None:
                    write_invalid_ticket(
                        details_file,
                        validation_result["record"]
                    )
                else:
                    invalid_records.append(
                        validation_result["record"]
                    )

                invalid_tickets_count += 1

                total_validation_error_count += (
                    validation_result["error_count"]
                )

        if details_file is not None:
            details_file.close()

    except BaseException:
        # A half-written details file is of no use to anyone.
        if details_file is not None:
            details_file.close()

            with contextlib.suppress(OSError):
                os.remove(details_file.name)

        raise

    logger.info(
        "Processed %d tickets in %.1fs: %d valid, %d invalid "
        "(%d validation errors)",
        total_tickets_count,
        time.monotonic() - started,
        valid_tickets_count,
        invalid_tickets_count,
        total_validation_error_count
    )

    result: ProcessingResult = {
        "filename": filename,

        "summary": summary,

        "valid_tickets_count":
            valid_tickets_count,

        "invalid_tickets_count":
            invalid_tickets_count,

        "total_tickets_count":
            total_tickets_count,

        "total_validation_error_count":
            total_validation_error_count,

        "invalid_records":
            invalid_records
    }

    if invalid_details_path is not None:
        result["invalid_details_path"] = str(invalid_details_path)

    return result
