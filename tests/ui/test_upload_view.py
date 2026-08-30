from unittest.mock import patch

from src.ui.upload_view import UploadView


def test_upload_view_creates_view_model(qtbot):
    view = UploadView()
    qtbot.addWidget(view)

    assert view.view_model is not None


def test_upload_view_initializes_selected_filename_to_none(qtbot):
    view = UploadView()
    qtbot.addWidget(view)

    assert view.selected_filename is None


def test_upload_view_creates_upload_button(qtbot):
    view = UploadView()
    qtbot.addWidget(view)

    assert view.upload_button is not None
    assert view.upload_button.text() == "Upload CSV File"


def test_upload_view_upload_button_is_enabled_initially(qtbot):
    view = UploadView()
    qtbot.addWidget(view)

    assert view.upload_button.isEnabled()


def test_upload_view_creates_hidden_error_message(qtbot):
    view = UploadView()
    qtbot.addWidget(view)

    assert view.error_message is not None
    assert view.error_message.isHidden()


def test_upload_view_has_expected_window_minimum_width_behavior(qtbot):
    view = UploadView()
    qtbot.addWidget(view)

    assert view.minimumWidth() == 0


def test_upload_view_emits_processing_started_when_file_is_selected(qtbot):
    view = UploadView()
    qtbot.addWidget(view)

    with patch(
        "src.ui.upload_view.QFileDialog.getOpenFileName",
        return_value=("C:/files/test.csv", "CSV Files (*.csv)")
    ), patch.object(
        view.view_model,
        "upload_file"
    ) as upload_file:

        with qtbot.waitSignal(
            view.processing_started,
            timeout=1000
        ):
            view.handle_upload_clicked()

        upload_file.assert_called_once_with(
            "C:/files/test.csv"
        )


def test_upload_view_stores_selected_filename(qtbot):
    view = UploadView()
    qtbot.addWidget(view)

    with patch(
        "src.ui.upload_view.QFileDialog.getOpenFileName",
        return_value=("C:/files/test.csv", "CSV Files (*.csv)")
    ), patch.object(
        view.view_model,
        "upload_file"
    ):

        view.handle_upload_clicked()

    assert view.selected_filename == "test.csv"


def test_upload_view_disables_upload_button_when_file_is_selected(qtbot):
    view = UploadView()
    qtbot.addWidget(view)

    with patch(
        "src.ui.upload_view.QFileDialog.getOpenFileName",
        return_value=("C:/files/test.csv", "CSV Files (*.csv)")
    ), patch.object(
        view.view_model,
        "upload_file"
    ):

        view.handle_upload_clicked()

    assert not view.upload_button.isEnabled()


def test_upload_view_does_nothing_when_file_selection_is_cancelled(qtbot):
    view = UploadView()
    qtbot.addWidget(view)

    with patch(
        "src.ui.upload_view.QFileDialog.getOpenFileName",
        return_value=("", "")
    ), patch.object(
        view.view_model,
        "upload_file"
    ) as upload_file:

        view.handle_upload_clicked()

    assert view.selected_filename is None
    assert view.upload_button.isEnabled()
    upload_file.assert_not_called()


def test_upload_view_hides_previous_error_when_new_file_is_selected(qtbot):
    view = UploadView()
    qtbot.addWidget(view)

    view.show_error("Previous error")

    assert not view.error_message.isHidden()

    with patch(
        "src.ui.upload_view.QFileDialog.getOpenFileName",
        return_value=("C:/files/test.csv", "CSV Files (*.csv)")
    ), patch.object(
        view.view_model,
        "upload_file"
    ):

        view.handle_upload_clicked()

    assert view.error_message.isHidden()


def test_upload_view_show_error_sets_message_and_shows_label(qtbot):
    view = UploadView()
    qtbot.addWidget(view)

    view.show_error("Something went wrong.")

    assert view.error_message.text() == "Something went wrong."
    assert not view.error_message.isHidden()


def test_upload_view_processing_error_reenables_upload_button(qtbot):
    view = UploadView()
    qtbot.addWidget(view)

    view.selected_filename = "test.csv"
    view.upload_button.setEnabled(False)

    with patch(
        "src.ui.upload_view.winsound.MessageBeep"
    ):
        view.show_processing_error("Invalid CSV file.")

    assert view.upload_button.isEnabled()


def test_upload_view_download_demo_file_does_nothing_when_cancelled(qtbot):
    view = UploadView()
    qtbot.addWidget(view)

    with patch(
        "src.ui.upload_view.QFileDialog.getSaveFileName",
        return_value=("", "")
    ), patch(
        "src.ui.upload_view.DemoFileService.download_demo_file"
    ) as download_demo_file:

        view.download_demo_file()

    download_demo_file.assert_not_called()


def test_upload_view_downloads_demo_file_to_selected_destination(qtbot):
    view = UploadView()
    qtbot.addWidget(view)

    with patch(
        "src.ui.upload_view.QFileDialog.getSaveFileName",
        return_value=("C:/files/demo.csv", "CSV Files (*.csv)")
    ), patch(
        "src.ui.upload_view.DemoFileService.download_demo_file"
    ) as download_demo_file:

        view.download_demo_file()

    download_demo_file.assert_called_once_with(
        "C:/files/demo.csv"
    )


def test_upload_view_shows_error_when_demo_file_download_fails(qtbot):
    view = UploadView()
    qtbot.addWidget(view)

    with patch(
        "src.ui.upload_view.QFileDialog.getSaveFileName",
        return_value=("C:/files/demo.csv", "CSV Files (*.csv)")
    ), patch(
        "src.ui.upload_view.DemoFileService.download_demo_file",
        side_effect=FileNotFoundError(
            "The demo file could not be found."
        )
    ):

        view.download_demo_file()

    assert view.error_message.text() == (
        "The demo file could not be found."
    )
    assert not view.error_message.isHidden()