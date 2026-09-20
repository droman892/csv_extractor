import pytest

from src.config import MAX_LINE_LENGTH
from src.processing.duplicates import find_duplicate_ticket_ids
from src.processing.csv_reader import (
    read_csv,
    validate_columns
)


def test_read_csv_returns_rows(tmp_path):
    csv_file = tmp_path / "test.csv"

    csv_file.write_text(
        "ticket_id,customer,priority,status,hours\n"
        "100000001,Acme Corp,high,open,2.5\n"
        "100000002,Globex,low,closed,1.0\n",
        encoding="utf-8"
    )

    result = list(read_csv(csv_file))

    assert result == [
        {
            "ticket_id": "100000001",
            "customer": "Acme Corp",
            "priority": "high",
            "status": "open",
            "hours": "2.5"
        },
        {
            "ticket_id": "100000002",
            "customer": "Globex",
            "priority": "low",
            "status": "closed",
            "hours": "1.0"
        }
    ]


def test_read_csv_handles_utf8_bom(tmp_path):
    csv_file = tmp_path / "test_bom.csv"

    csv_file.write_text(
        "\ufeffticket_id,customer,priority,status,hours\n"
        "100000001,Acme Corp,high,open,2.5\n",
        encoding="utf-8"
    )

    result = list(read_csv(csv_file))

    assert result == [
        {
            "ticket_id": "100000001",
            "customer": "Acme Corp",
            "priority": "high",
            "status": "open",
            "hours": "2.5"
        }
    ]


def test_read_csv_raises_file_not_found_error(tmp_path):
    csv_file = tmp_path / "does_not_exist.csv"

    with pytest.raises(FileNotFoundError):
        list(read_csv(csv_file))


def test_validate_columns_accepts_required_columns():
    fieldnames = [
        "ticket_id",
        "status",
        "priority",
        "customer",
        "hours"
    ]

    validate_columns(fieldnames)


def test_validate_columns_rejects_missing_column():
    fieldnames = [
        "ticket_id",
        "status",
        "priority",
        "customer"
    ]

    with pytest.raises(ValueError, match="hours"):
        validate_columns(fieldnames)


def test_validate_columns_reports_multiple_missing_columns():
    fieldnames = [
        "ticket_id",
        "customer"
    ]

    with pytest.raises(
        ValueError,
        match="hours.*priority.*status"
    ):
        validate_columns(fieldnames)


# -------------------------------------------------------------------
# one record per line
# -------------------------------------------------------------------

HEADER = "ticket_id,customer,priority,status,hours\n"


def write_csv(tmp_path, body):
    csv_file = tmp_path / "test.csv"

    csv_file.write_text(
        HEADER + body,
        encoding="utf-8",
        newline=""
    )

    return csv_file


def test_read_csv_skips_blank_lines(tmp_path):
    csv_file = write_csv(
        tmp_path,
        "100000001,Acme Corp,high,open,2.5\n"
        "\n"
        "   \n"
        "100000002,Globex,low,closed,1.0\n"
        "\n"
    )

    result = list(read_csv(csv_file))

    assert [row["ticket_id"] for row in result] == [
        "100000001",
        "100000002"
    ]
    assert all("_csv_error" not in row for row in result)


def test_read_csv_accepts_crlf_and_a_missing_final_newline(tmp_path):
    csv_file = write_csv(
        tmp_path,
        "100000001,Acme Corp,high,open,2.5\r\n"
        "100000002,Globex,low,closed,1.0"
    )

    result = list(read_csv(csv_file))

    assert len(result) == 2
    assert result[1]["hours"] == "1.0"
    assert all("_csv_error" not in row for row in result)


def test_read_csv_treats_a_multi_line_quoted_field_as_bad_lines(
    tmp_path
):
    csv_file = write_csv(
        tmp_path,
        '100000001,"Acme\nCorp",high,open,2.5\n'
        "100000002,Globex,low,closed,1.0\n"
    )

    result = list(read_csv(csv_file))

    assert len(result) == 3

    assert "_csv_error" in result[0]
    assert "_csv_error" in result[1]
    assert "_csv_error" not in result[2]

    assert "each record must be on a single line" in (
        result[0]["_csv_error"]
    )


def test_read_csv_puts_the_file_line_number_in_the_error(tmp_path):
    csv_file = write_csv(
        tmp_path,
        "100000001,Acme Corp,high,open,2.5\n"
        "\n"
        "100000002,Globex,low\n"
    )

    result = list(read_csv(csv_file))

    # The header is line 1 and the blank line is line 3.
    assert result[1]["_csv_error"] == (
        "Line 4: expected 5 fields, found 3"
    )


def test_read_csv_keeps_the_raw_line_of_a_bad_row(tmp_path):
    csv_file = write_csv(
        tmp_path,
        '100000001,"Acme,high,open,2.5\n'
    )

    row = list(read_csv(csv_file))[0]

    assert row["_csv_line"] == '100000001,"Acme,high,open,2.5'


def test_read_csv_shortens_a_long_bad_line(tmp_path):
    # Under the line limit but long: kept in the report only in part.
    csv_file = write_csv(
        tmp_path,
        '100000001,"' + "x" * (MAX_LINE_LENGTH - 100) + "\n"
    )

    row = list(read_csv(csv_file))[0]

    assert "unbalanced" in row["_csv_error"]
    assert len(row["_csv_line"]) < 300
    assert row["_csv_line"].endswith("...")


def test_read_csv_accepts_quoted_commas_and_escaped_quotes(tmp_path):
    csv_file = write_csv(
        tmp_path,
        '100000001,"Acme, ""Corp"" Ltd",high,open,2.5\n'
    )

    row = list(read_csv(csv_file))[0]

    assert "_csv_error" not in row
    assert row["customer"] == 'Acme, "Corp" Ltd'


def test_read_csv_rejects_files_over_the_row_limit(
    tmp_path,
    monkeypatch
):
    monkeypatch.setattr(
        "src.processing.csv_reader.MAX_DATA_ROWS",
        2
    )

    csv_file = write_csv(
        tmp_path,
        "100000001,A,high,open,1.0\n"
        "100000002,B,high,open,1.0\n"
        "100000003,C,high,open,1.0\n"
    )

    with pytest.raises(ValueError, match="more than 2 data rows"):
        list(read_csv(csv_file))


def test_read_csv_rejects_an_empty_file(tmp_path):
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="header"):
        list(read_csv(csv_file))


def test_read_csv_rejects_a_file_with_the_wrong_columns(tmp_path):
    csv_file = tmp_path / "wrong.csv"
    csv_file.write_text("a,b,c\n1,2,3\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Missing required columns"):
        list(read_csv(csv_file))


# A data line of exactly `length` characters (not counting the line
# break): a valid row whose customer is padded with spaces to fit.
def line_of_length(length):
    row = "100000001,Acme,high,open,1.0"
    return row + " " * (length - len(row))


@pytest.mark.parametrize("line_break", ["\n", "\r\n", "\r"])
@pytest.mark.parametrize(
    "offset, too_long",
    [(-1, False), (0, False), (1, True), (2, True), (3, True)]
)
def test_read_csv_line_length_limit(
    tmp_path,
    line_break,
    offset,
    too_long
):
    # offset is the line's length relative to the limit.
    length = MAX_LINE_LENGTH + offset
    csv_file = tmp_path / "limit.csv"
    csv_file.write_bytes(
        (
            "ticket_id,customer,priority,status,hours" + line_break
            + line_of_length(length) + line_break
            + "100000002,Globex,low,closed,2.0" + line_break
        ).encode("utf-8")
    )

    rows = list(read_csv(csv_file))

    # The line after it is always read, and is line 3 of the file.
    assert len(rows) == 2
    assert rows[1]["ticket_id"] == "100000002"
    assert "_csv_error" not in rows[1]

    if too_long:
        assert "_csv_error" in rows[0]
        assert rows[0]["_csv_error"].startswith(
            f"Line 2: longer than {MAX_LINE_LENGTH:,}"
        )
    else:
        assert "_csv_error" not in rows[0]


def test_read_csv_reports_a_line_number_after_a_long_line(tmp_path):
    # A "\r\n" line break can be cut in half by the read size.
    csv_file = write_csv(
        tmp_path,
        line_of_length(MAX_LINE_LENGTH + 1) + "\r\n"
        + "100000002,Globex,low,closed\r\n"
    )

    rows = list(read_csv(csv_file))

    assert rows[1]["_csv_error"].startswith("Line 3:")


def test_read_csv_a_long_line_at_the_end_of_the_file(tmp_path):
    csv_file = write_csv(tmp_path, "x" * (MAX_LINE_LENGTH * 5))

    rows = list(read_csv(csv_file))

    assert len(rows) == 1
    assert "longer than" in rows[0]["_csv_error"]


def test_read_csv_a_very_long_line_is_skipped_in_pieces(tmp_path):
    # Several times the size of one skipped piece, with the default size.
    csv_file = write_csv(
        tmp_path,
        "x" * 200_000 + "\r\n"
        + "100000002,Globex,low,closed,2.0\r\n"
    )

    rows = list(read_csv(csv_file))

    assert len(rows) == 2
    assert len(rows[0]["_csv_line"]) < 300
    assert rows[1]["ticket_id"] == "100000002"


def test_read_csv_skipping_in_tiny_pieces_finds_the_line_end(
    tmp_path,
    monkeypatch
):
    # The rest of a long line is skipped in pieces. With tiny pieces
    # the loop must still find the end of the line.
    monkeypatch.setattr(
        "src.processing.csv_reader.SKIP_CHUNK_SIZE",
        7
    )

    csv_file = write_csv(
        tmp_path,
        "x" * (MAX_LINE_LENGTH * 2) + "\n"
        + "100000002,Globex,low,closed,2.0\n"
    )

    rows = list(read_csv(csv_file))

    assert len(rows) == 2
    assert rows[1]["ticket_id"] == "100000002"


@pytest.mark.parametrize("line_break", ["\n", "\r\n", "\r"])
def test_read_csv_skipping_stops_at_every_kind_of_line_break(
    tmp_path,
    monkeypatch,
    line_break
):
    # Try every position of the line break relative to the piece size.
    monkeypatch.setattr(
        "src.processing.csv_reader.SKIP_CHUNK_SIZE",
        4
    )

    for extra in range(0, 12):
        csv_file = tmp_path / f"skip_{extra}.csv"
        csv_file.write_bytes(
            (
                "ticket_id,customer,priority,status,hours" + line_break
                + "y" * (MAX_LINE_LENGTH + 1 + extra) + line_break
                + "100000002,Globex,low,closed,2.0" + line_break
            ).encode("utf-8")
        )

        rows = list(read_csv(csv_file))

        assert len(rows) == 2, extra
        assert rows[1]["ticket_id"] == "100000002"


def test_read_csv_rejects_a_header_longer_than_the_limit(tmp_path):
    csv_file = tmp_path / "header.csv"
    csv_file.write_text(
        "ticket_id,customer,priority,status,hours,"
        + "x" * MAX_LINE_LENGTH
        + "\n100000001,Acme,high,open,1.0\n",
        encoding="utf-8"
    )

    with pytest.raises(ValueError, match="header row is longer than"):
        list(read_csv(csv_file))


def test_read_csv_a_long_line_counts_toward_the_row_limit(
    tmp_path,
    monkeypatch
):
    monkeypatch.setattr(
        "src.processing.csv_reader.MAX_DATA_ROWS",
        2
    )

    long_line = "x" * (MAX_LINE_LENGTH * 3) + "\n"

    csv_file = write_csv(tmp_path, long_line * 3)

    with pytest.raises(ValueError, match="more than 2 data rows"):
        list(read_csv(csv_file))


def test_read_csv_a_long_line_is_not_a_duplicate_of_anything(tmp_path):
    csv_file = write_csv(
        tmp_path,
        "100000001," + "x" * (MAX_LINE_LENGTH * 2) + "\n"
        + "100000001,Acme,high,open,1.0\n"
    )

    assert find_duplicate_ticket_ids(csv_file) == {}
