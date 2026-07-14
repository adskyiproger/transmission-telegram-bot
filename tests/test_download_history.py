import json
from pathlib import Path

from models.DownloadHistory import DownloadHistory


def test_history_uses_structured_records(tmp_path: Path):
    path = tmp_path / "history.jsonl"
    original = DownloadHistory.download_log_file
    try:
        DownloadHistory.set_log_file(str(path))
        DownloadHistory.add("2026-07-14", "name, with comma\nand newline", "/data", 42)

        stored = json.loads(path.read_text(encoding="utf-8"))
        assert stored["name"] == "name, with comma and newline"
        assert DownloadHistory.show() == [stored]
    finally:
        DownloadHistory.set_log_file(original)
