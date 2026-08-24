from unittest.mock import patch
from src.ui.view_models.upload_view_model import UploadViewModel


def test_upload_file_emits_processing_failed_on_value_error():
    view_model = UploadViewModel()

    received_errors = []

    view_model.processing_failed.connect(
        received_errors.append
    )

    with patch(
        "src.ui.view_models.upload_view_model.process_csv",
        side_effect=ValueError("Missing required columns: customer, hours, priority, status, ticket_id")
    ):
        view_model.upload_file("invalid.csv")

    assert received_errors == [
        "Missing required columns: customer, hours, priority, status, ticket_id"
    ]