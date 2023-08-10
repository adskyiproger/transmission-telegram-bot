from lib.func import trans, bytes_to_human
from models.Browser import Browser


class HistoryBrowser(Browser):
    def get_page(self, _page: int = None) -> str:
        if not _page:
            _page = self.prev_page

        page = int(_page)
        self.prev_page = page
        _message = trans("DOWNLOAD_HISTORY_NAV", self.user_lang).format(page, self.number_of_pages, len(self.posts)) + "\n"
        # Add first and last posts index
        post_num = (page - 1) * self.posts_per_page
        for post in self.posts[post_num:post_num+self.posts_per_page]:
            log_item = post.split(',')
            # 'date': log_item[0],
            # 'name': log_item[1],
            # 'size': log_item[2]
            if len(log_item) == 4:
                _message += f"{log_item[0]} <b>{log_item[1]}</b>: {bytes_to_human(log_item[3])}\n"
            post_num += 1
        return _message
