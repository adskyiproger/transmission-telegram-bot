import os
import json
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from lib.func import get_logger

log = get_logger("DownloadHistory")


@dataclass(frozen=True)
class DownloadRecord:
    date_done: str
    name: str
    download_dir: str
    size_when_done: int


class DownloadHistory:
    download_log_file = "download.log"
    _lock = threading.Lock()

    @staticmethod
    def show():
        if not os.path.isfile(DownloadHistory.download_log_file):
            log.warning("File %s doesn't exist", DownloadHistory.download_log_file)
            return []
        with open(DownloadHistory.download_log_file, "r", encoding="utf-8") as f:
            records = []
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    # Backward compatibility with the original comma-separated log.
                    fields = [field.strip() for field in line.rsplit(",", 3)]
                    if len(fields) == 4:
                        records.append(
                            {
                                "date_done": fields[0],
                                "name": fields[1],
                                "download_dir": fields[2],
                                "size_when_done": fields[3],
                            }
                        )
            return records

    @staticmethod
    def set_log_file(download_log_file):
        DownloadHistory.download_log_file = download_log_file

    @staticmethod
    def add(date_done, name, download_dir, size_when_done):
        try:
            DownloadHistory._update_file(
                DownloadRecord(
                    date_done=str(date_done),
                    name=str(name).replace("\n", " "),
                    download_dir=str(download_dir),
                    size_when_done=int(size_when_done),
                )
            )
        except Exception as err:
            log.error(
                "Failed write into the file log history file %s: %s",
                DownloadHistory.download_log_file,
                err,
            )

    @staticmethod
    def _update_file(item: DownloadRecord):
        path = Path(DownloadHistory.download_log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        with DownloadHistory._lock, path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")
