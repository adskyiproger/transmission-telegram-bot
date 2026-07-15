from html import escape

from lib.func import trans, bytes_to_human
from models.Browser import Browser


class HistoryBrowser(Browser):
    def get_page(self, _page: int | None = None) -> str:
        if not _page:
            _page = self.prev_page

        page = int(_page)
        self.prev_page = page
        _message = trans("DOWNLOAD_HISTORY_NAV", self.user_lang).format(
            page, self.number_of_pages, self.len
        )

        # Add first and last posts index
        post_num = (page - 1) * self.posts_per_page
        post_end = post_num + self.posts_per_page
        for post in self.posts[post_num:post_end]:
            if isinstance(post, dict):
                _message += (
                    f"{escape(str(post['date_done']))} "
                    f"<b>{escape(str(post['name']))}</b>: "
                    f"{bytes_to_human(post['size_when_done'])}\n"
                )
            post_num += 1
        return _message
