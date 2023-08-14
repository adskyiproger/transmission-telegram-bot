from lib.func import trans
from models.Browser import Browser


class PostsBrowser(Browser):
    def get_page(self, _page: int = None) -> str:
        if not _page:
            _page = self.prev_page

        page = int(_page)
        self.prev_page = page
        _message = trans("NAV_HEADER", self.user_lang).format(page, self.number_of_pages, self.len)
        # Add first and last posts index
        post_num = (page - 1) * self.posts_per_page
        for post in self.posts[post_num:post_num+self.posts_per_page]:
            _message += f"\n<b>{post['title']}</b>: {post['size']}  {post['date']} ⬆{post['seed']} ⬇{post['leach']}\n" \
                        f"<a href='{post['info']}'>Info</a>     [ ▼ /download_{post_num} ]\n"
            post_num += 1
        return _message
