from lib.func import trans, bytes_to_human
from models.Browser import Browser
from transmission_rpc.torrent import Torrent

class TorrentInfoBrowser(Browser):

    def __init__(self, user_id: int = None, user_lang: str = "en", posts: Torrent = None, posts_per_page: int = 5) -> None:
        self.user_id = user_id
        self.user_lang = user_lang
        self.posts = posts.files()
        self.id = posts.id
        self.name = posts.name
        self.posts_per_page = posts_per_page
        self.prev_page = 1

    @property
    def len(self):
        return len(self.posts)

    def get_page(self, _page: int = None) -> str:
        if not _page:
            _page = self.prev_page

        page = int(_page)
        self.prev_page = page
        
        # Add first and last posts index
        post_num = (page - 1) * self.posts_per_page
        _message = f"<b>{self.name}</b>: "+trans("TORRENT_INFO_PAGE_HEADER", self.user_lang).format(page,
                                                                                                    self.number_of_pages,
                                                                                                    len(self.posts))
        _message += " [▶ /start_{0}] [⏹ /stop_{0}] [⏏ /delete_{0}]".format(self.id)
        _message += "\n--------------\n"

        for file in self.posts[post_num:post_num+self.posts_per_page]:
            _message += f"{file.name}: completed/size: {bytes_to_human(file.completed)}/{bytes_to_human(file.size)} Bytes \n"
            post_num += 1
        return _message
