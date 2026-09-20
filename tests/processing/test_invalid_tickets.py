import pytest

from src.processing.invalid_tickets import (
    iter_invalid_tickets,
    open_for_writing,
    read_invalid_tickets,
    write_invalid_ticket
)


ERROR = {
    "field": "priority",
    "invalid_value": "urgent",
    "reason": "Invalid priority."
}


def test_tickets_written_to_a_file_are_read_back_in_order(tmp_path):
    path = tmp_path / "invalid.jsonl"

    with open_for_writing(path) as file:
        write_invalid_ticket(file, {"ticket_id": "1", "errors": [ERROR]})
        write_invalid_ticket(file, {"ticket_id": "2", "errors": []})

    assert list(read_invalid_tickets(path)) == [
        {"ticket_id": "1", "errors": [ERROR]},
        {"ticket_id": "2", "errors": []}
    ]


def test_only_the_id_and_errors_are_written(tmp_path):
    path = tmp_path / "invalid.jsonl"

    with open_for_writing(path) as file:
        write_invalid_ticket(
            file,
            {
                "ticket_id": "1",
                "customer": "Acme",
                "hours": 2.5,
                "errors": [ERROR]
            }
        )

    assert list(read_invalid_tickets(path)) == [
        {"ticket_id": "1", "errors": [ERROR]}
    ]


def test_a_ticket_without_errors_is_written_with_an_empty_list(tmp_path):
    path = tmp_path / "invalid.jsonl"

    with open_for_writing(path) as file:
        write_invalid_ticket(file, {"ticket_id": "1"})

    assert list(read_invalid_tickets(path)) == [
        {"ticket_id": "1", "errors": []}
    ]


def test_a_value_json_cannot_store_is_written_as_text(tmp_path):
    path = tmp_path / "invalid.jsonl"

    odd = {"field": "hours", "invalid_value": {1, 2}, "reason": "x"}

    with open_for_writing(path) as file:
        write_invalid_ticket(file, {"ticket_id": "1", "errors": [odd]})

    (ticket,) = read_invalid_tickets(path)

    assert ticket["errors"][0]["invalid_value"] == "{1, 2}"


def test_opening_will_not_overwrite_an_existing_file(tmp_path):
    path = tmp_path / "invalid.jsonl"
    path.write_text("keep me")

    with pytest.raises(FileExistsError):
        open_for_writing(path)

    assert path.read_text() == "keep me"


def test_reading_a_missing_file_says_the_list_is_gone(tmp_path):
    with pytest.raises(ValueError, match="no longer available"):
        list(read_invalid_tickets(tmp_path / "gone.jsonl"))


def test_iter_uses_the_file_when_there_is_one(tmp_path):
    path = tmp_path / "invalid.jsonl"

    with open_for_writing(path) as file:
        write_invalid_ticket(file, {"ticket_id": "9", "errors": [ERROR]})

    result = {
        "invalid_records": [],
        "invalid_details_path": str(path)
    }

    assert [t["ticket_id"] for t in iter_invalid_tickets(result)] == ["9"]


def test_iter_uses_the_list_when_there_is_no_file():
    result = {
        "invalid_records": [{"ticket_id": "5", "errors": [ERROR]}]
    }

    assert [t["ticket_id"] for t in iter_invalid_tickets(result)] == ["5"]


def test_closing_the_iterator_early_closes_the_file(tmp_path):
    path = tmp_path / "invalid.jsonl"

    with open_for_writing(path) as file:
        for number in range(5):
            write_invalid_ticket(
                file,
                {"ticket_id": str(number), "errors": [ERROR]}
            )

    tickets = read_invalid_tickets(path)
    next(tickets)
    tickets.close()

    # A file that is still open cannot be deleted on Windows.
    path.unlink()

    assert not path.exists()
