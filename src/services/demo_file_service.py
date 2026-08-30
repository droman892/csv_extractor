from pathlib import Path

class DemoFileService:
    @staticmethod
    def get_demo_file_path():
        return (
            Path(__file__).resolve().parents[2]
            / "data"
            / "demo_data.csv"
        )

    @staticmethod
    def demo_file_exists():
        return DemoFileService.get_demo_file_path().is_file()

    @staticmethod
    def download_demo_file(destination_path):
        source_path = DemoFileService.get_demo_file_path()

        if not source_path.is_file():
            raise FileNotFoundError(
                "The test file could not be found."
            )

        Path(destination_path).write_bytes(
            source_path.read_bytes()
        )