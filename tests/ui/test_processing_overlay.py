from PySide6.QtTest import QTest

from src.ui.processing_overlay import Spinner, ProcessingOverlay


def test_spinner_initializes_with_zero_angle(qtbot):
    spinner = Spinner()
    qtbot.addWidget(spinner)

    assert spinner.angle == 0


def test_spinner_has_expected_size(qtbot):
    spinner = Spinner()
    qtbot.addWidget(spinner)

    assert spinner.width() == 48
    assert spinner.height() == 48


def test_spinner_timer_initially_inactive(qtbot):
    spinner = Spinner()
    qtbot.addWidget(spinner)

    assert not spinner.timer.isActive()


def test_spinner_start_activates_timer(qtbot):
    spinner = Spinner()
    qtbot.addWidget(spinner)

    spinner.start()

    assert spinner.timer.isActive()

    spinner.stop()


def test_spinner_stop_deactivates_timer(qtbot):
    spinner = Spinner()
    qtbot.addWidget(spinner)

    spinner.start()
    spinner.stop()

    assert not spinner.timer.isActive()


def test_spinner_rotate_increases_angle(qtbot):
    spinner = Spinner()
    qtbot.addWidget(spinner)

    spinner.rotate()

    assert spinner.angle == 30


def test_spinner_rotate_wraps_angle_at_360(qtbot):
    spinner = Spinner()
    qtbot.addWidget(spinner)

    spinner.angle = 330

    spinner.rotate()

    assert spinner.angle == 0


def test_processing_overlay_initializes_hidden(qtbot):
    overlay = ProcessingOverlay()
    qtbot.addWidget(overlay)

    assert overlay.isHidden()


def test_processing_overlay_creates_spinner(qtbot):
    overlay = ProcessingOverlay()
    qtbot.addWidget(overlay)

    assert isinstance(overlay.spinner, Spinner)
    assert overlay.spinner.parent() is overlay


def test_processing_overlay_start_shows_overlay_and_starts_spinner(qtbot):
    overlay = ProcessingOverlay()
    qtbot.addWidget(overlay)

    overlay.resize(800, 600)
    overlay.start()

    assert overlay.isVisible()
    assert overlay.spinner.timer.isActive()

    overlay.stop()


def test_processing_overlay_stop_hides_overlay_and_stops_spinner(qtbot):
    overlay = ProcessingOverlay()
    qtbot.addWidget(overlay)

    overlay.start()
    overlay.stop()

    assert overlay.isHidden()
    assert not overlay.spinner.timer.isActive()


def test_processing_overlay_positions_spinner_in_center(qtbot):
    overlay = ProcessingOverlay()
    qtbot.addWidget(overlay)

    overlay.resize(800, 600)
    overlay.start()

    expected_x = (
        (overlay.width() - overlay.spinner.width()) // 2
    )

    expected_y = (
        (overlay.height() - overlay.spinner.height()) // 2
    )

    assert overlay.spinner.x() == expected_x
    assert overlay.spinner.y() == expected_y

    overlay.stop()


def test_processing_overlay_repositions_spinner_on_resize(qtbot):
    overlay = ProcessingOverlay()
    qtbot.addWidget(overlay)

    overlay.resize(800, 600)
    overlay.show()

    overlay.resize(1000, 700)

    QTest.qWait(50)

    expected_x = (
        (overlay.width() - overlay.spinner.width()) // 2
    )

    expected_y = (
        (overlay.height() - overlay.spinner.height()) // 2
    )

    assert overlay.spinner.x() == expected_x
    assert overlay.spinner.y() == expected_y


def test_processing_overlay_spinner_rotates_while_running(qtbot):
    overlay = ProcessingOverlay()
    qtbot.addWidget(overlay)

    overlay.start()

    initial_angle = overlay.spinner.angle

    QTest.qWait(100)

    assert overlay.spinner.angle != initial_angle

    overlay.stop()