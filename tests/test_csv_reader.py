import pytest
from src.csv_reader import read_csv

def test_read_csv_returns_rows(tmp_path):
    csv_file = tmp_path / "test.csv"

    csv_file.write_text(
        "ticket_id,customer,priority,status,hours\n"
        "1001,Acme Corp,high,open,2.5\n"
        "1002,Globex,low,closed,1.0\n",
        encoding="utf-8"
    )

    result = read_csv(csv_file)

    assert result == [
        {
            "ticket_id": "1001",
            "customer": "Acme Corp",
            "priority": "high",
            "status": "open",
            "hours": "2.5"
        },
        {
            "ticket_id": "1002",
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
        "1001,Acme Corp,high,open,2.5\n",
        encoding="utf-8"
    )

    result = read_csv(csv_file)

    assert result == [
        {
            "ticket_id": "1001",
            "customer": "Acme Corp",
            "priority": "high",
            "status": "open",
            "hours": "2.5"
        }
    ]

def test_read_csv_raises_file_not_found_error(tmp_path):
    csv_file = tmp_path / "does_not_exist.csv"

    with pytest.raises(FileNotFoundError):
        read_csv(csv_file)