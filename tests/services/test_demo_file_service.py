from pathlib import Path

import pytest

from src.services.demo_file_service import DemoFileService


def test_get_demo_file_path_returns_expected_path():
    path = DemoFileService.get_demo_file_path()

    assert isinstance(path, Path)
    assert path.name == "demo_data.csv"
    assert path.parent.name == "data"


def test_demo_file_exists_returns_true_when_demo_file_exists(
    tmp_path,
    monkeypatch
):
    demo_file = tmp_path / "data" / "demo_data.csv"
    demo_file.parent.mkdir()
    demo_file.write_text("test data")

    monkeypatch.setattr(
        DemoFileService,
        "get_demo_file_path",
        staticmethod(lambda: demo_file)
    )

    assert DemoFileService.demo_file_exists() is True


def test_demo_file_exists_returns_false_when_demo_file_does_not_exist(
    tmp_path,
    monkeypatch
):
    demo_file = tmp_path / "data" / "demo_data.csv"

    monkeypatch.setattr(
        DemoFileService,
        "get_demo_file_path",
        staticmethod(lambda: demo_file)
    )

    assert DemoFileService.demo_file_exists() is False


def test_download_demo_file_copies_demo_file(
    tmp_path,
    monkeypatch
):
    source_file = tmp_path / "source" / "demo_data.csv"
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
        DemoFileService,
        "get_demo_file_path",
        staticmethod(lambda: source_file)
    )

    DemoFileService.download_demo_file(
        destination_file
    )

    assert destination_file.is_file()
    assert (
        destination_file.read_bytes()
        == source_file.read_bytes()
    )


def test_download_demo_file_raises_error_when_source_does_not_exist(
    tmp_path,
    monkeypatch
):
    source_file = (
        tmp_path
        / "source"
        / "demo_data.csv"
    )

    destination_file = (
        tmp_path
        / "destination"
        / "demo.csv"
    )

    monkeypatch.setattr(
        DemoFileService,
        "get_demo_file_path",
        staticmethod(lambda: source_file)
    )

    with pytest.raises(
        FileNotFoundError,
        match="The test file could not be found."
    ):
        DemoFileService.download_demo_file(
            destination_file
        )