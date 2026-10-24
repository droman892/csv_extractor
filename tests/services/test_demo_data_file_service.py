import pytest

from csv_extractor.services.demo_data_file_service import DemoDataFileService


def test_demo_data_file_ships_with_the_package():
    path = DemoDataFileService.get_demo_data_file_path()

    assert path.name == "demo_data_file.csv"
    assert path.is_file()
    assert path.read_text(encoding="utf-8-sig").startswith("ticket_id,")


def test_demo_data_file_exists_returns_true_when_demo_data_file_exists(
    tmp_path,
    monkeypatch
):
    demo_data_file = tmp_path / "data" / "demo_data_file.csv"
    demo_data_file.parent.mkdir()
    demo_data_file.write_text("test data")

    monkeypatch.setattr(
        DemoDataFileService,
        "get_demo_data_file_path",
        staticmethod(lambda: demo_data_file)
    )

    assert DemoDataFileService.demo_data_file_exists() is True


def test_demo_data_file_exists_returns_false_when_demo_data_file_does_not_exist(
    tmp_path,
    monkeypatch
):
    demo_data_file = tmp_path / "data" / "demo_data_file.csv"

    monkeypatch.setattr(
        DemoDataFileService,
        "get_demo_data_file_path",
        staticmethod(lambda: demo_data_file)
    )

    assert DemoDataFileService.demo_data_file_exists() is False


def test_download_demo_data_file_copies_demo_data_file(
    tmp_path,
    monkeypatch
):
    source_file = tmp_path / "source" / "demo_data_file.csv"
    source_file.parent.mkdir()
    source_file.write_bytes(
        b"ticket_id,customer\n123,Acme"
    )

    destination_directory = tmp_path / "destination"
    destination_directory.mkdir()

    destination_file = (
        destination_directory / "demo.csv"
    )

    monkeypatch.setattr(
        DemoDataFileService,
        "get_demo_data_file_path",
        staticmethod(lambda: source_file)
    )

    DemoDataFileService.download_demo_data_file(
        destination_file
    )

    assert destination_file.is_file()
    assert (
        destination_file.read_bytes()
        == source_file.read_bytes()
    )


def test_download_demo_data_file_raises_error_when_source_does_not_exist(
    tmp_path,
    monkeypatch
):
    source_file = (
        tmp_path
        / "source"
        / "demo_data_file.csv"
    )

    destination_file = (
        tmp_path
        / "destination"
        / "demo.csv"
    )

    monkeypatch.setattr(
        DemoDataFileService,
        "get_demo_data_file_path",
        staticmethod(lambda: source_file)
    )

    with pytest.raises(
        FileNotFoundError,
        match="The demo data file could not be found."
    ):
        DemoDataFileService.download_demo_data_file(
            destination_file
        )