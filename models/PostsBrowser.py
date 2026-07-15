from html import escape
from urllib.parse import urlparse

from lib.func import trans
from models.Browser import Browser


class PostsBrowser(Browser):
    def get_page(self, _page: int | None = None) -> str:
        if not _page:
            _page = self.prev_page

        page = int(_page)
        self.prev_page = page
        _message = trans("NAV_HEADER", self.user_lang).format(
            page, self.number_of_pages, self.len
        )
        # Add first and last posts index
        post_num = (page - 1) * self.posts_per_page
        post_end = post_num + self.posts_per_page
        for post in self.posts[post_num:post_end]:
            info_url = str(post["info"])
            if urlparse(info_url).scheme not in {"http", "https"}:
                info_url = ""
            _message += (
                f"\n<b>{escape(str(post['title']))}</b>: \n"
                f"{escape(str(post['size']))}  {escape(str(post['date']))} "
                f"⬆{escape(str(post['seed']))} ⬇{escape(str(post['leach']))}\n"
                f"<a href='{escape(info_url, quote=True)}'>"
                f"🌐{escape(str(post['tracker']))}</a> "
                f"🧲/torrent_{post_num} ➕/download_{post_num}\n"
            )
            post_num += 1
        return _message
