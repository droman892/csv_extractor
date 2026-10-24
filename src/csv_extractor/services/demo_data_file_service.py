from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path


class DemoDataFileService:
    @staticmethod
    def get_demo_data_file_path() -> Traversable:
        # The sample file ships inside the package, so the same lookup works
        # from a clone, from an install, and from the PyInstaller build
        # (csv_extractor.spec collects the package's data files).
        return files("csv_extractor") / "resources" / "demo_data_file.csv"

    @staticmethod
    def demo_data_file_exists() -> bool:
        return DemoDataFileService.get_demo_data_file_path().is_file()

    @staticmethod
    def download_demo_data_file(destination_path: str | Path) -> None:
        source_path = DemoDataFileService.get_demo_data_file_path()

        if not source_path.is_file():
            raise FileNotFoundError(
                "The demo data file could not be found."
            )

        Path(destination_path).write_bytes(
            source_path.read_bytes()
        )
