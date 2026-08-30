from unittest.mock import MagicMock, patch

from PySide6.QtCore import Qt

from src.ui.results_view import ResultsView


RESULT = {
    "filename": "test.csv",
    "total_tickets_count": 10,
    "valid_tickets_count": 8,
    "invalid_tickets_count": 2,
    "summary": {
        "total_hours": 20.0,
        "tickets_by_status": {
            "open": 6,
            "closed": 4
        },
        "tickets_by_priority": {
            "high": 5,
            "medium": 3,
            "low": 2
        },
        "hours_by_customer": {
            "Acme Corp": 12.0,
            "Globex": 8.0
        }
    },
    "invalid_records": [
        {
            "ticket_id": "1001",
            "field": "priority",
            "invalid_value": "urgent",
            "reason": "Priority must be low, medium, or high."
        },
        {
            "ticket_id": "1002",
            "field": "hours",
            "invalid_value": "45",
            "reason": "Hours must be between 0 and 40."
        }
    ],
    "total_customer_count": 2,
    "total_invalid_record_count": 2,
    "total_invalid_error_count": 2
}


def test_results_view_initializes_with_view_model(qtbot):
    view = ResultsView(
        RESULT,
        RESULT
    )
    qtbot.addWidget(view)

    assert view.view_model is not None


def test_results_view_stores_filename(qtbot):
    view = ResultsView(
        RESULT,
        RESULT
    )
    qtbot.addWidget(view)

    assert view.filename == "test.csv"


def test_results_view_creates_results_title(qtbot):
    view = ResultsView(
        RESULT,
        RESULT
    )
    qtbot.addWidget(view)

    assert view.results_title is not None


def test_results_view_results_title_contains_filename(qtbot):
    view = ResultsView(
        RESULT,
        RESULT
    )
    qtbot.addWidget(view)

    qtbot.waitUntil(
        lambda: "test.csv" in view.results_title.text()
    )

    assert "test.csv" in view.results_title.text()


def test_results_view_creates_status_table(qtbot):
    view = ResultsView(
        RESULT,
        RESULT
    )
    qtbot.addWidget(view)

    assert view.status_table is not None
    assert view.status_table.rowCount() == 2
    assert view.status_table.columnCount() == 2


def test_results_view_creates_priority_table(qtbot):
    view = ResultsView(
        RESULT,
        RESULT
    )
    qtbot.addWidget(view)

    assert view.priority_table is not None
    assert view.priority_table.rowCount() == 3
    assert view.priority_table.columnCount() == 2


def test_results_view_creates_customer_table(qtbot):
    view = ResultsView(
        RESULT,
        RESULT
    )
    qtbot.addWidget(view)

    assert view.customer_table is not None
    assert view.customer_table.rowCount() == 2
    assert view.customer_table.columnCount() == 2


def test_results_view_creates_validation_table(qtbot):
    view = ResultsView(
        RESULT,
        RESULT
    )
    qtbot.addWidget(view)

    assert view.validation_table is not None
    assert view.validation_table.rowCount() == 2
    assert view.validation_table.columnCount() == 4


def test_results_view_displays_status_values(qtbot):
    view = ResultsView(
        RESULT,
        RESULT
    )
    qtbot.addWidget(view)

    assert view.status_table.item(0, 0).text() == "Open"
    assert view.status_table.item(1, 0).text() == "Closed"


def test_results_view_displays_priority_values(qtbot):
    view = ResultsView(
        RESULT,
        RESULT
    )
    qtbot.addWidget(view)

    values = [
        view.priority_table.item(row, 0).text()
        for row in range(view.priority_table.rowCount())
    ]

    assert values == [
        "High",
        "Medium",
        "Low"
    ]