


class DownloadHistory():
    def show():
        with open("myfile.txt", "r",  encoding="utf-8") as f:
            return f.readlines()

    def add(date_done, name, download_dir, size_when_done):
        # self.items.append({date_done, name, download_dir, size_when_done})
        DownloadHistory._update_file(f"{date_done}, {name}, {download_dir}, {size_when_done}")

    def _update_file(item):
        with open("myfile.txt", "a", encoding="utf-8") as f:
            f.write(str(item) + "\n")