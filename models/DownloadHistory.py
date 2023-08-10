from lib.func import get_logger

log = get_logger("DownloadHistory")

class DownloadHistory():
    download_log_file = 'download.log'
    def show():
        logs = ''
        with open(DownloadHistory.download_log_file, "r",  encoding="utf-8") as f:
            logs = (str(f.read()))
        return logs.split('\n')

    def set_log_file(download_log_file):
        DownloadHistory.download_log_file = download_log_file

    def add(date_done, name, download_dir, size_when_done):
        try:
            DownloadHistory._update_file(f"{date_done}, {name}, {download_dir}, {size_when_done}")
        except Exception as err:
            log.error("Failed write into the file log history file %s: %s", DownloadHistory.download_log_file, err)

    def _update_file(item):
        with open(DownloadHistory.download_log_file, "a", encoding="utf-8") as f:
            f.write(str(item) + "\n")
