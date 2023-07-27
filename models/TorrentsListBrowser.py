from lib.func import trans
from models.Browser import Browser


class TorrentsListBrowser(Browser):
    def get_page(self, _page: int = None) -> str:
        if not _page:
            _page = self.prev_page

        page = int(_page)
        self.prev_page = page
        _message = trans("TORRENT_LIST_HEADER", self.user_lang).format(page, self.number_of_pages, self.len)
        _message += "\n---------------------\n"
        post_num = (page - 1) * self.posts_per_page
        for torrent in self.posts[post_num:post_num+self.posts_per_page]:        
            _message += f"\n<b>{torrent.name}</b>\n"
            _status = trans(torrent.status, self.user_lang)
            _message += trans("PROGRESS_STATUS",self.user_lang).format(f"{round(torrent.progress)}%", _status)
            if torrent.status in ['seeding', 'downloading']:
                _message += "\n[ℹ /info_{0}] [⏹  /stop_{0}] [⏏ /delete_{0}]\n".format(torrent.id)
            else:
                _message += "\n[ℹ /info_{0}] [▶ /start_{0}] [⏏ /delete_{0}]\n".format(torrent.id)
            post_num += 1
        return _message
