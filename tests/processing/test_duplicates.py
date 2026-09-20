import pytest

from src.processing.duplicates import find_duplicate_ticket_ids


HEADER = "ticket_id,customer,priority,status,hours\n"


def write_csv(tmp_path, *lines):
    csv_file = tmp_path / "tickets.csv"

    csv_file.write_text(
        HEADER + "".join(line + "\n" for line in lines),
        encoding="utf-8"
    )

    return csv_file


def test_returns_empty_when_every_ticket_id_is_unique(tmp_path):
    csv_file = write_csv(
        tmp_path,
        "100000001,Acme,high,open,2.5",
        "100000002,Globex,low,closed,1.0"
    )

    assert find_duplicate_ticket_ids(csv_file) == {}


def test_counts_how_often_each_repeated_id_appears(tmp_path):
    csv_file = write_csv(
        tmp_path,
        "100000001,Acme,high,open,2.5",
        "100000002,Globex,low,closed,1.0",
        "100000001,Initech,low,open,1.0",
        "100000003,Acme,high,open,2.5",
        "100000001,Globex,medium,closed,3.0",
        "100000002,Acme,high,open,2.5"
    )

    assert find_duplicate_ticket_ids(csv_file) == {
        "100000001": 3,
        "100000002": 2
    }


def test_matches_ids_that_differ_only_by_surrounding_spaces(tmp_path):
    csv_file = write_csv(
        tmp_path,
        "100000001,Acme,high,open,2.5",
        " 100000001 ,Globex,low,closed,1.0"
    )

    assert find_duplicate_ticket_ids(csv_file) == {"100000001": 2}


def test_counts_a_repeated_id_even_when_the_row_is_otherwise_invalid(
    tmp_path
):
    csv_file = write_csv(
        tmp_path,
        "100000001,Acme,high,open,2.5",
        "100000001,,urgent,open,-1"
    )

    assert find_duplicate_ticket_ids(csv_file) == {"100000001": 2}


def test_ignores_repeated_ids_that_are_not_valid_ids(tmp_path):
    csv_file = write_csv(
        tmp_path,
        "ABC,Acme,high,open,2.5",
        "ABC,Globex,low,closed,1.0",
        ",Acme,high,open,2.5",
        ",Acme,high,open,2.5"
    )

    assert find_duplicate_ticket_ids(csv_file) == {}


def test_ignores_malformed_rows(tmp_path):
    csv_file = write_csv(
        tmp_path,
        "100000001,Acme,high,open,2.5",
        '100000001,"Globex,low,closed,1.0'
    )

    assert find_duplicate_ticket_ids(csv_file) == {}


def test_ignores_blank_lines(tmp_path):
    csv_file = write_csv(
        tmp_path,
        "100000001,Acme,high,open,2.5",
        "",
        "100000002,Globex,low,closed,1.0"
    )

    assert find_duplicate_ticket_ids(csv_file) == {}


def test_raises_file_not_found_for_a_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        find_duplicate_ticket_ids(tmp_path / "missing.csv")
