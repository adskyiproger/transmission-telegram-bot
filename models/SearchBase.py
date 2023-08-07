import requests

from lib.func import get_logger

class SearchBase:
    SESSION = requests.Session()
    LOGGED_IN = False
    POSTS = []
    TRACKER_NAME = 'dummy'
    _log = None

    def __init__(self, username, password) -> None:
        self.username = username
        self.password = password
        self.POSTS = []

    async def search(self) -> bool:
        pass

    @property
    def log(self):
        if not self._log:
            self._log = get_logger(self.__class__.__name__)
        return self._log
