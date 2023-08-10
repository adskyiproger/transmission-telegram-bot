from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from lib.func import get_logger

class Browser:
    def __init__(self, user_id: int = None, user_lang: str = "en", posts: dict = None, posts_per_page: int = 5) -> None:
        self.user_id = user_id
        self.user_lang = user_lang
        self.posts = posts
        self.posts_per_page = posts_per_page
        self.prev_page = 1

    @property
    def len(self):
        return len(self.posts)

    @property
    def log(self):
        if not self._log:
            self._log = get_logger(self.__class__.__name__)
        return self._log

    @property
    def number_of_pages(self) -> int:
        num_pages = int(len(self.posts) / self.posts_per_page)
        if len(self.posts) % self.posts_per_page > 0:
            num_pages += 1
        return num_pages

    def get_page(self, _page: int = None) -> str:
        return f"Not Implemented method {_page}"

    def get_keyboard(self, _page: int = None) -> InlineKeyboardMarkup:
        pages = self.number_of_pages
        # Edge case for first page
        if not _page:
            _page = self.prev_page

        page = int(_page)
        self.prev_page = page

        if pages == 1:
            KEYBOARD = []
        elif page == 1 or page < 4:
            KEYBOARD = [InlineKeyboardButton(str(jj), callback_data=str(jj)) for jj in range(1, 8) if 0 < jj <= pages]
        # Edge case for last page
        elif pages - page < 4:
            KEYBOARD = [InlineKeyboardButton(str(jj), callback_data=str(jj)) for jj in range(pages - 6, pages + 1) if 0 < jj <= pages]
        # Regular navigation
        else:
            KEYBOARD = [InlineKeyboardButton(str(jj), callback_data=str(jj)) for jj in range(page - 3, page + 4) if 0 < jj <= pages]

        FOOTER_KEYS = []
        if page > 10:
            FOOTER_KEYS.append(InlineKeyboardButton("«« -10", callback_data=str(page-10)))
        if pages > page + 10:
            FOOTER_KEYS.append(InlineKeyboardButton("+10 »»", callback_data=str(page+10)))

        for key in KEYBOARD:
            if str(key.text) == str(page):
                idx = KEYBOARD.index(key)
                KEYBOARD.remove(key)
                KEYBOARD.insert(idx, InlineKeyboardButton("...", callback_data="x"))
                break

        return InlineKeyboardMarkup([KEYBOARD, FOOTER_KEYS])
