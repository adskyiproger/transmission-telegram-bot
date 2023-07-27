from lib.func import trans
from models.Browser import Browser


class TorrentsListBrowser(Browser):
    def get_page(self, _page: int = None) -> str:
        if not _page:
            _page = self.prev_page

        page = int(_page)
        self.prev_page = page
        _message = trans("Torrents list", self.user_lang)+": \n"
        post_num = (page - 1) * self.posts_per_page
        for torrent in self.posts[post_num:post_num+self.posts_per_page]:
            if torrent.status in ['seeding', 'downloading']:
                _message += "\n<b>{1}</b>\n Progress: {2}% Status: {3} \n[ℹ /info_{0}] [⏹  /stop_{0}] [⏏ /delete_{0}]\n" \
                    .format(torrent.id, torrent.name, round(torrent.progress), torrent.status)
            else:
                _message += "\n<b>{1}</b>\n Progress: {2}% Status: {3} \n[ℹ /info_{0}] [▶ /start_{0}] [⏏ /delete_{0}]\n" \
                    .format(torrent.id, torrent.name, round(torrent.progress), torrent.status)
            post_num += 1
        return _message
